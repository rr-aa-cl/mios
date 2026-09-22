"""Run IRQ tuning against fake commands and temporary proc/sys files only."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "pin_franka_nic_irq.sh"

FAKE_COMMAND = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

root = Path(os.environ["FAKE_IRQ_ROOT"])
config = json.loads((root / "config.json").read_text())
command, arguments = Path(sys.argv[0]).name, sys.argv[1:]
with (root / "calls.jsonl").open("a") as log:
    log.write(json.dumps([command, *arguments]) + "\n")
if command == "ip":
    assert arguments == ["route", "get", os.environ["ROBOT_IP"]], arguments
    print(config["route"])
elif command == "ps":
    assert arguments == ["-eLo", "tid=,comm="], arguments
    print(config["threads"])
elif command == "ethtool":
    if arguments[0] == "--coalesce" and "replacement_irqs" in config:
        directory = root / "fake-sys/class/net" / arguments[1] / "device/msi_irqs"
        for entry in directory.iterdir():
            entry.unlink()
        for irq in config["replacement_irqs"]:
            (directory / str(irq)).touch()
elif command != "chrt":
    raise AssertionError(command)
'''


class PinFrankaIRQTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sysroot = self.root / "fake-sys"
        self.procroot = self.root / "fake-proc"
        self.procroot.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("ip", "ps", "ethtool", "chrt"):
            command = self.bin / name
            command.write_text(FAKE_COMMAND)
            command.chmod(0o755)

        # Exercise the script without root: change only its EUID guard and
        # absolute pseudo-filesystem roots in a temporary copy. The real
        # /proc and /sys paths never reach the executed test script.
        source = SCRIPT.read_text()
        self.assertEqual(source.count("${EUID}"), 1)
        source = source.replace("${EUID}", "0")
        source = source.replace("/sys/", str(self.sysroot) + "/")
        source = source.replace("/proc/", str(self.procroot) + "/")
        self.assertNotIn("/sys/", source)
        self.assertNotIn("/proc/", source)
        self.script = self.root / "pin_irq.sh"
        self.script.write_text(source)

        self.environment = dict(os.environ,
                                PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                                FAKE_IRQ_ROOT=str(self.root), ROBOT_IP="192.168.3.100",
                                MIOS_CONTROL_CPU="6", MIOS_FRANKA_IRQ_PRIORITY="90")
        self.config = {"route": "192.168.3.100 dev enp3s0 src 192.168.3.1 uid 0\n    cache",
                       "threads": ""}
        self.interrupts = ""
        self.affinities = {}

    def add_irq(self, irq, *, interface="enp3s0", msi=True, affinity=True):
        if msi:
            directory = self.sysroot / "class/net" / interface / "device/msi_irqs"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / str(irq)).touch()
        if affinity:
            path = self.procroot / "irq" / str(irq) / "smp_affinity_list"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("0-15\n")
            self.affinities[irq] = path

    def run_helper(self, *, success=True):
        (self.root / "config.json").write_text(json.dumps(self.config))
        (self.root / "calls.jsonl").write_text("")
        (self.procroot / "interrupts").write_text(self.interrupts)
        result = subprocess.run(["bash", str(self.script)], env=self.environment,
                                capture_output=True, text=True, timeout=5, check=False)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.calls = [json.loads(line) for line in (self.root / "calls.jsonl").read_text().splitlines()]
        self.mutations = [call for call in self.calls if call[0] in ("ethtool", "chrt")]
        return result

    def assert_no_mutation(self):
        self.assertEqual(self.mutations, [])
        for path in self.affinities.values():
            self.assertEqual(path.read_text(), "0-15\n")

    def test_msi_vectors_include_igc_queues_and_truncated_thread_names(self):
        self.environment.update(MIOS_CONTROL_CPU="3", MIOS_FRANKA_IRQ_PRIORITY="88")
        for irq in range(105, 110):
            self.add_irq(irq)
        self.add_irq(777, msi=False)
        self.interrupts = "777: 0 0 PCI-MSI enp3s0\n"  # Sysfs is authoritative.
        directory = self.sysroot / "class/net/enp3s0/device/msi_irqs"
        (directory / "not-an-irq").touch()
        self.config["threads"] = "\n".join(
            f"{2000 + irq} " + f"irq/{irq}-enp3s0-TxRx-{irq - 106}"[:15]
            for irq in range(105, 110))
        self.config["threads"] += "\n2106 irq/106-enp3s0-\n9999 irq/1060-other"

        self.run_helper()

        for irq in range(105, 110):
            self.assertEqual(self.affinities[irq].read_text(), "3\n")
        self.assertEqual(self.affinities[777].read_text(), "0-15\n")
        self.assertEqual([call for call in self.calls if call[0] == "chrt"], [
            ["chrt", "--fifo", "--pid", "88", str(2000 + irq)] for irq in range(105, 110)])
        self.assertEqual([call for call in self.calls if call[0] == "ethtool"], [
            ["ethtool", "--set-eee", "enp3s0", "eee", "off"],
            ["ethtool", "--pause", "enp3s0", "autoneg", "off", "rx", "off", "tx", "off"],
            ["ethtool", "--coalesce", "enp3s0", "rx-usecs", "0"],
        ])

    def test_legacy_fallback_matches_exact_and_queue_names_without_duplicates(self):
        for irq in (105, 106, 107):
            self.add_irq(irq, msi=False)
        self.interrupts = ("105: 0 0 IO-APIC enp3s0\n"
                           "106: 0 0 PCI-MSI enp3s0-TxRx-0,enp3s0-TxRx-0\n"
                           "106: 0 0 PCI-MSI enp3s0-TxRx-0\n"
                           "107: 0 0 PCI-MSI enp3s01-TxRx-0\n")
        self.config["threads"] = "2105 irq/105-enp3s0\n2106 irq/106-enp3s0-"

        result = self.run_helper()

        self.assertEqual(self.affinities[105].read_text(), "6\n")
        self.assertEqual(self.affinities[106].read_text(), "6\n")
        self.assertEqual(self.affinities[107].read_text(), "0-15\n")
        self.assertEqual(result.stdout.count("Pinned IRQ"), 2)
        self.assertEqual([call for call in self.calls if call[0] == "chrt"], [
            ["chrt", "--fifo", "--pid", "90", "2105"],
            ["chrt", "--fifo", "--pid", "90", "2106"],
        ])

    def test_gateway_loopback_and_missing_device_routes_reject_before_mutation(self):
        self.add_irq(105)
        for route in ("192.168.3.100 via 10.180.68.1 dev enp3s0 src 10.180.68.124",
                      "192.168.3.100 dev lo src 192.168.3.100",
                      "local 192.168.3.100 dev lo src 192.168.3.100",
                      "192.168.3.100 src 192.168.3.1"):
            with self.subTest(route=route):
                self.config["route"] = route
                result = self.run_helper(success=False)
                self.assertIn("direct, non-loopback route", result.stderr)
                self.assert_no_mutation()

    def test_no_irqs_rejects_before_nic_settings_or_affinity_changes(self):
        self.add_irq(107, msi=False)
        self.interrupts = "107: 0 0 PCI-MSI enp3s01-TxRx-0\n"

        result = self.run_helper(success=False)

        self.assertIn("No IRQs found", result.stderr)
        self.assert_no_mutation()

    def test_all_affinity_files_are_preflighted_before_any_mutation(self):
        self.add_irq(105)
        self.add_irq(106, affinity=False)

        result = self.run_helper(success=False)

        self.assertIn("Cannot write", result.stderr)
        self.assert_no_mutation()

    def test_driver_renumbering_uses_rediscovered_irqs_after_ethtool(self):
        self.add_irq(105)
        for irq in (205, 206):
            self.add_irq(irq, msi=False)
        self.config["replacement_irqs"] = [205, 206]
        self.config["threads"] = "2105 irq/105-enp3s0\n2205 irq/205-enp3s0-\n2206 irq/206-enp3s0-"

        self.run_helper()

        self.assertEqual(self.affinities[105].read_text(), "0-15\n")
        self.assertEqual(self.affinities[205].read_text(), "6\n")
        self.assertEqual(self.affinities[206].read_text(), "6\n")
        self.assertEqual([call[-1] for call in self.calls if call[0] == "chrt"], ["2205", "2206"])

    def test_irqs_disappearing_after_nic_settings_never_receive_stale_writes(self):
        self.add_irq(105)
        self.config["replacement_irqs"] = []

        result = self.run_helper(success=False)

        self.assertIn("No IRQs found", result.stderr)
        self.assertEqual(self.affinities[105].read_text(), "0-15\n")
        self.assertEqual(len([call for call in self.calls if call[0] == "ethtool"]), 3)
        self.assertFalse(any(call[0] == "chrt" for call in self.calls))


if __name__ == "__main__":
    unittest.main()
