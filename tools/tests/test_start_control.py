"""Exercise the actual Control supervisor with harmless child processes."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
START = ROOT / "docker/ros2/start_control.sh"
HEALTH = ROOT / "docker/ros2/check_control_ready.sh"

FAKE_PROCESS = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(os.environ["FAKE_CONTROL_ROOT"])
role = "launch" if Path(sys.argv[0]).name == "ros2" else "prepare"
if len(sys.argv) > 1 and sys.argv[1] == "child":
    role = "child"
stopped = False
def stop(number, frame):
    global stopped
    (root / (role + ".signal")).write_text(str(number))
    stopped = True
signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
(root / (role + ".pid")).write_text(str(os.getpid()))
(root / (role + ".args")).write_text(json.dumps(sys.argv[1:]))
child = None
if role == "launch" and os.environ.get("FAKE_CHILD") == "1":
    child = subprocess.Popen([sys.executable, sys.argv[0], "child"])
code = 0
while not stopped:
    if role == "prepare" and (root / "prepare.release").exists():
        code = int(os.environ.get("FAKE_PREPARE_EXIT", "0"))
        break
    if role == "launch" and (root / "launch.exit").exists():
        code = 3
        break
    time.sleep(0.01)
if child is not None:
    child.wait(timeout=2)
(root / (role + ".exited")).write_text(str(code))
sys.exit(code)
'''


class ControlStartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        for name in ("ros2", "start_model_broadcaster.sh"):
            path = self.bin / name
            path.write_text(FAKE_PROCESS)
            path.chmod(0o755)
        taskset = self.bin / "taskset"
        taskset.write_text('#!/usr/bin/env bash\nset -eu\n'
                           '[[ "$1" == --cpu-list && "$2" == "$MIOS_CONTROL_WORKER_CPUS" ]]\n'
                           'shift 2\nexec "$@"\n')
        taskset.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        FAKE_CONTROL_ROOT=str(self.directory),
                        MIOS_CONTROL_STATE_DIR=str(self.directory / "state"),
                        MIOS_CONTROL_WORKER_CPUS="0,2", ROBOT_IP="192.0.2.5",
                        MIOS_LOAD_GRIPPER="false")
        self.process = None
        self.log = (self.directory / "output").open("w+")

    def tearDown(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                # Only processes created by this fixture can appear here.
                for role in ("launch", "prepare"):
                    path = self.directory / (role + ".pid")
                    if path.exists():
                        try:
                            os.killpg(int(path.read_text()), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                self.process.kill()
                self.process.wait(timeout=2)
        self.log.close()
        self.temp.cleanup()

    def start(self, **env):
        self.env.update(env)
        self.process = subprocess.Popen(["bash", str(START)], env=self.env,
                                        stdout=self.log, stderr=subprocess.STDOUT)

    def wait_for(self, relative):
        path = self.directory / relative
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            if path.exists() and path.stat().st_size:
                return path
            if self.process is not None and self.process.poll() is not None:
                break
            time.sleep(0.01)
        self.fail(f"Did not observe {relative}; output: " + (self.directory / "output").read_text())

    def release(self):
        (self.directory / "prepare.release").touch()

    def healthy(self):
        return subprocess.run(["bash", str(HEALTH)], env=self.env, capture_output=True,
                              timeout=2).returncode == 0

    def assert_stopped(self, code):
        self.assertEqual(code, self.process.wait(timeout=4), (self.directory / "output").read_text())
        self.assertFalse(self.healthy())
        self.assertFalse((self.directory / "state/ready").exists())

    def test_readiness_waits_for_preparation_and_passes_configuration(self):
        self.start()
        self.wait_for("prepare.pid")
        self.wait_for("launch.pid")
        self.assertFalse(self.healthy())
        self.release()
        self.wait_for("state/ready")
        self.assertTrue(self.healthy())
        args = json.loads((self.directory / "launch.args").read_text())
        self.assertEqual(args[:3], ["launch", "franka_bringup", "franka.launch.py"])
        self.assertIn("robot_ip:=192.0.2.5", args)
        self.assertIn("load_gripper:=false", args)
        self.assertIn("controllers_yaml:=/ws/install/mios_ros2_control/share/mios_ros2_control/config/mios_controllers.yaml", args)

    def test_preparation_failure_stops_launch_without_readiness(self):
        self.start(FAKE_PREPARE_EXIT="1")
        self.wait_for("launch.pid")
        self.wait_for("prepare.pid")
        self.release()
        self.assert_stopped(1)
        self.assertEqual(str(signal.SIGINT), (self.directory / "launch.signal").read_text())

    def test_launch_failure_cancels_pending_preparation(self):
        self.start()
        self.wait_for("launch.pid")
        self.wait_for("prepare.pid")
        (self.directory / "launch.exit").touch()
        self.assert_stopped(1)
        self.assertEqual(str(signal.SIGTERM), (self.directory / "prepare.signal").read_text())

    def test_launch_failure_after_readiness_fails_container_and_removes_marker(self):
        self.start()
        self.release()
        self.wait_for("state/ready")
        (self.directory / "launch.exit").touch()
        self.assert_stopped(1)

    def test_termination_during_setup_cancels_both_children(self):
        state = self.directory / "state"
        state.mkdir()
        (state / "ready").write_text("stale marker\n")
        self.start()
        self.wait_for("launch.pid")
        self.wait_for("prepare.pid")
        self.assertFalse((state / "ready").exists())
        self.process.terminate()
        self.assert_stopped(143)
        self.assertTrue((self.directory / "prepare.exited").exists())
        self.assertTrue((self.directory / "launch.exited").exists())

    def test_termination_reaches_launch_descendants(self):
        self.start(FAKE_CHILD="1")
        self.wait_for("child.pid")
        self.release()
        self.wait_for("state/ready")
        self.process.terminate()
        self.assert_stopped(143)
        self.assertEqual(str(signal.SIGINT), (self.directory / "child.signal").read_text())
        self.assertTrue((self.directory / "child.exited").exists())

    def test_health_rejects_reused_pid_and_malformed_markers(self):
        state = self.directory / "state"
        state.mkdir()
        marker = state / "ready"
        for value in ("", "garbage\n", "0 123\n", f"{os.getpid()} 0\n", f"{os.getpid()} 1 extra\n"):
            with self.subTest(value=value):
                marker.write_text(value)
                self.assertFalse(self.healthy())

    def test_invalid_gripper_gate_fails_before_starting_children(self):
        self.start(MIOS_LOAD_GRIPPER="maybe")
        self.assert_stopped(2)
        self.assertFalse((self.directory / "launch.pid").exists())
        self.assertFalse((self.directory / "prepare.pid").exists())


if __name__ == "__main__":
    unittest.main()
