"""Exercise the shared start-script helpers and the Core readiness check."""
import os
from pathlib import Path
import socket
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "docker/common/runtime_lib.sh"
CORE_READY = ROOT / "docker/core/check_core_ready.sh"


def run(script, **environment):
    return subprocess.run(["bash", "-c", f"set -euo pipefail; source '{LIB}'; {script}"],
                          capture_output=True, text=True, timeout=30,
                          env=dict(os.environ, **environment))


class RuntimeLibTests(unittest.TestCase):
    def test_cpu_list_expands_ranges_and_removes_duplicates(self):
        result = run('expand_cpu_list "0-2,4, 7-8,2"')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["0", "1", "2", "4", "7", "8"], result.stdout.split())

    def test_invalid_cpu_lists_are_rejected(self):
        for value in ("", "-1", "2-1", "0-1-2", "all", "1,,2", "1,"):
            with self.subTest(value=value):
                self.assertNotEqual(0, run(f'expand_cpu_list "{value}"').returncode)

    def test_pin_applies_exactly_the_requested_cpus(self):
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 2:
            self.skipTest("needs two usable CPUs")
        wanted = f"{cpus[0]},{cpus[1]}"
        result = run(f'pin_to_cpus "{wanted}"; taskset --cpu-list --pid $$')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({cpus[0], cpus[1]},
                         {int(part) for part in
                          result.stdout.rsplit(":", 1)[1].replace("-", ",").split(",")})

    def test_pin_fails_when_a_requested_cpu_is_unavailable(self):
        cpus = sorted(os.sched_getaffinity(0))
        missing = (os.cpu_count() or 1) + 64
        result = run(f'pin_to_cpus "{cpus[0]},{missing}"')
        self.assertNotEqual(0, result.returncode)
        self.assertRegex(result.stderr, "Requested CPUs|Cannot pin")

    def test_wait_is_skipped_for_zero_and_finds_an_open_port(self):
        self.assertEqual(0, run("wait_for_ports 0 1").returncode)
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            port = server.getsockname()[1]
            result = run(f"wait_for_ports 5 {port}")
            self.assertEqual(0, result.returncode, result.stderr)
            ready = subprocess.run(["bash", str(CORE_READY)], timeout=10,
                                   env=dict(os.environ, MIOS_WS_PORT=str(port)))
            self.assertEqual(0, ready.returncode)

    def test_wait_and_core_readiness_fail_on_a_closed_port(self):
        with socket.socket() as placeholder:
            placeholder.bind(("127.0.0.1", 0))
            port = placeholder.getsockname()[1]
        result = run(f"wait_for_ports 2 {port}")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unavailable", result.stderr)
        ready = subprocess.run(["bash", str(CORE_READY)], capture_output=True, timeout=10,
                               env=dict(os.environ, MIOS_WS_PORT=str(port)))
        self.assertNotEqual(0, ready.returncode)


if __name__ == "__main__":
    unittest.main()
