"""Host readiness checks against synthetic procfs/sysfs and command results."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deployment_readiness.common import CommandResult, Context
from deployment_readiness.host import collect, parse_cpu_list


class FixtureRunner:
    def __init__(self):
        self.calls = []
        self.routes = [{"dst": "192.168.4.100", "dev": "eth1", "prefsrc": "192.168.4.1"}]
        self.defaults = [{"dev": "eth0", "gateway": "10.0.0.1"}]
        self.ps = " 42 FF 90 irq/136-eth1\n"
        self.ping_result = CommandResult(0, "5 packets transmitted, 5 received, 0% packet loss, time 800ms\n")
        self.overrides = {}

    def run(self, argv, timeout=10, input=None):
        self.calls.append((argv, timeout))
        if tuple(argv) in self.overrides:
            return self.overrides[tuple(argv)]
        if argv[:5] == ["ip", "-j", "-4", "route", "get"]:
            return CommandResult(0, json.dumps(self.routes))
        if argv == ["ip", "-j", "-4", "route", "show", "default"]:
            return CommandResult(0, json.dumps(self.defaults))
        if argv[0] == "ps":
            return CommandResult(0, self.ps)
        if argv[:2] == ["ethtool", "--show-eee"]:
            return CommandResult(0, "EEE status: disabled\n")
        if argv[:2] == ["ethtool", "--show-coalesce"]:
            return CommandResult(0, "Adaptive RX: off  TX: off\nrx-usecs: 0\n")
        if argv[:2] == ["ethtool", "--show-pause"]:
            return CommandResult(0, "RX: off\nTX: off\n")
        if argv[0] == "ping":
            return self.ping_result
        raise AssertionError(f"Unexpected command: {argv}")


class HostChecksTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.context = Context(repo_root=self.root, sys_root=self.root / "sys", proc_root=self.root / "proc",
                               kernel_config_path=self.root / "boot/config", profile="motion")
        self.runner = FixtureRunner()
        self.write("sys/kernel/realtime", "1")
        self.write("sys/devices/system/cpu/online", "0-19")
        self.write("sys/devices/system/cpu/isolated", "6-7")
        self.write("sys/devices/system/cpu/cpu6/topology/thread_siblings_list", "6-7")
        for cpu in (6, 7):
            self.write(f"sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor", "performance")
            for number, latency, disabled in ((0, 0, 0), (1, 1, 0), (2, 1048, 1)):
                self.write(f"sys/devices/system/cpu/cpu{cpu}/cpuidle/state{number}/latency", str(latency))
                self.write(f"sys/devices/system/cpu/cpu{cpu}/cpuidle/state{number}/disable", str(disabled))
        for name, value in {"type": "1", "operstate": "up", "carrier": "1", "speed": "1000", "duplex": "full"}.items():
            self.write(f"sys/class/net/eth1/{name}", value)
        self.write("sys/class/net/eth1/device/msi_irqs/136", "msi")
        self.write("proc/interrupts", "136: 0 10 0 PCI-MSI eth1-TxRx-0\n")
        self.write("proc/irq/136/effective_affinity_list", "6")

    def write(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)

    def findings(self):
        return {check.id: check for check in collect(self.context, self.runner)}

    def test_commissioned_host_passes_without_mutating_commands(self):
        checks = self.findings()
        self.assertTrue(checks)
        self.assertEqual({item.status for item in checks.values()}, {"PASS"})
        for command, timeout in self.runner.calls:
            self.assertIn(command[0], {"ip", "ps", "ethtool", "ping"})
            self.assertLessEqual(timeout, 5)
            self.assertNotIn("sudo", command)
        self.assertIn("does not validate FCI timing", checks["host.robot_ping"].message)

    def test_power_policy_is_strict_only_for_motion(self):
        self.write("sys/devices/system/cpu/cpu6/cpufreq/scaling_governor", "powersave")
        self.write("sys/devices/system/cpu/cpu7/cpuidle/state2/disable", "0")
        for profile, expected in (("motion", "FAIL"), ("state-only", "WARN")):
            with self.subTest(profile=profile):
                self.context.profile = profile
                checks = self.findings()
                self.assertEqual(checks["host.cpu_governor"].status, expected)
                self.assertEqual(checks["host.cpu_idle"].status, expected)

    def test_unreadable_power_policy_cannot_pass_motion(self):
        (self.root / "sys/devices/system/cpu/cpu6/cpufreq/scaling_governor").unlink()
        (self.root / "sys/devices/system/cpu/cpu7/cpuidle/state0/disable").unlink()
        checks = self.findings()
        self.assertEqual(checks["host.cpu_governor"].status, "UNKNOWN")
        self.assertEqual(checks["host.cpu_idle"].status, "UNKNOWN")

    def test_worker_or_nonrt_overlap_with_sibling_fails(self):
        for field in ("worker_cpus", "nonrt_cpus"):
            with self.subTest(field=field):
                original = getattr(self.context, field)
                setattr(self.context, field, "0-5,7-19")
                self.assertEqual(self.findings()["host.cpu_siblings"].status, "FAIL")
                setattr(self.context, field, original)

    def test_offline_and_unisolated_cpu_fail(self):
        self.write("sys/devices/system/cpu/online", "0-18")
        self.write("sys/devices/system/cpu/isolated", "6")
        checks = self.findings()
        self.assertEqual(checks["host.cpu_online"].status, "FAIL")
        self.assertEqual(checks["host.cpu_isolation"].status, "FAIL")

    def test_kernel_configuration_fallback_and_unknown(self):
        (self.root / "sys/kernel/realtime").unlink()
        self.assertEqual(self.findings()["host.realtime_kernel"].status, "UNKNOWN")
        self.write("boot/config", "CONFIG_PREEMPT_RT=y\n")
        self.assertEqual(self.findings()["host.realtime_kernel"].status, "PASS")
        self.write("boot/config", "CONFIG_PREEMPT=y\n# CONFIG_PREEMPT_RT is not set\n")
        self.assertEqual(self.findings()["host.realtime_kernel"].status, "FAIL")

    def test_gateway_route_rejected_before_network_probe(self):
        self.runner.routes[0]["gateway"] = "192.168.4.1"
        self.assertEqual(self.findings()["host.robot_route"].status, "FAIL")
        self.assertFalse(any(command[0] == "ping" for command, _ in self.runner.calls))

    def test_shared_default_route_fails(self):
        self.runner.defaults.append({"dev": "eth1", "gateway": "192.168.4.1"})
        self.assertEqual(self.findings()["host.nic_dedicated"].status, "FAIL")

    def test_link_fault_and_unknown_are_not_ready(self):
        self.write("sys/class/net/eth1/speed", "100")
        self.assertEqual(self.findings()["host.nic_link"].status, "FAIL")
        (self.root / "sys/class/net/eth1/speed").unlink()
        self.assertEqual(self.findings()["host.nic_link"].status, "UNKNOWN")

    def test_effective_affinity_precedes_configured_affinity(self):
        self.write("proc/irq/136/smp_affinity_list", "6")
        self.write("proc/irq/136/effective_affinity_list", "0-19")
        self.assertEqual(self.findings()["host.nic_irq_affinity"].status, "FAIL")

    def test_queue_named_interrupt_detected_without_sysfs_msi(self):
        (self.root / "sys/class/net/eth1/device/msi_irqs/136").unlink()
        self.assertEqual(self.findings()["host.nic_irq_affinity"].status, "PASS")

    def test_irq_priority_and_visibility(self):
        self.runner.ps = "42 FF 80 irq/136-eth1\n"
        self.assertEqual(self.findings()["host.nic_irq_priority"].status, "FAIL")
        self.runner.ps = "42 TS - ordinary-process\n"
        self.assertEqual(self.findings()["host.nic_irq_priority"].status, "UNKNOWN")

    def test_missing_commands_and_bad_json_report_unknown(self):
        key = ("ip", "-j", "-4", "route", "get", self.context.robot_ip)
        for result in (CommandResult(127, stderr="ip not found"), CommandResult(0, "{}"), CommandResult(0, "not JSON")):
            with self.subTest(output=result):
                self.runner.overrides[key] = result
                self.assertEqual(self.findings()["host.robot_route"].status, "UNKNOWN")

    def test_packet_loss_fails_and_disabled_ping_warns(self):
        self.runner.ping_result = CommandResult(1, "5 packets transmitted, 4 received, 20% packet loss\n")
        self.assertEqual(self.findings()["host.robot_ping"].status, "FAIL")
        self.context.ping = False
        self.runner.calls.clear()
        self.assertEqual(self.findings()["host.robot_ping"].status, "WARN")
        self.assertFalse(any(command[0] == "ping" for command, _ in self.runner.calls))

    def test_optional_nic_tuning_failure_is_visible_warning(self):
        self.runner.overrides[("ethtool", "--show-eee", "eth1")] = CommandResult(95, stderr="Operation not supported")
        self.assertEqual(self.findings()["host.nic_eee"].status, "WARN")

    def test_cpu_list_rejects_bad_ranges(self):
        self.assertEqual(parse_cpu_list("0-2,6,8-9"), {0, 1, 2, 6, 8, 9})
        for value in ("7-6", "0-999999999999", "6--7", "-1", "6,", "a"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_cpu_list(value)


if __name__ == "__main__":
    unittest.main()
