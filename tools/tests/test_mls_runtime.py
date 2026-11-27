"""Offline MLS supervisor, ownership, and probe checks; no system changes."""

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[2] / "docker/ml_service/mls_runtime.py"
SPEC = importlib.util.spec_from_file_location("mls_runtime_tested", SOURCE)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class MlsRuntimeTests(unittest.TestCase):
    ENV = {
        "MIOS_NONRT_CPUS": "0-5,8-19",
        "MONGO_PORT": "27018",
        "MIOS_WS_PORT": "13000",
        "MIOS_ML_PORT": "8100",
        "MIOS_STARTUP_WAIT_SECONDS": "180",
    }

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(mock.patch.dict(runtime.os.environ, self.ENV, clear=True))
        self.events = []
        self.requested_affinity = None
        self.actual_affinity = None
        self.affinity = self.patch(runtime.os, "sched_setaffinity", self.set_affinity)
        self.read_affinity = self.patch(runtime.os, "sched_getaffinity", self.get_affinity)
        self.execv = self.patch(runtime.os, "execv", self.record("execv"))
        self.execvp = self.patch(runtime.os, "execvp", self.record("execvp"))
        self.popen = self.patch(runtime.subprocess, "Popen", AssertionError("Unexpected process launch"))
        self.signals = self.patch(runtime.signal, "signal", AssertionError("Unexpected signal handler change"))
        self.killpg = self.patch(runtime.os, "killpg", self.record("killpg"))
        self.paths = self.patch(runtime, "Path", AssertionError("Unexpected filesystem inspection"))
        self.marker = mock.MagicMock()
        self.stack.enter_context(mock.patch.object(runtime, "MLS_PID_FILE", self.marker))
        self.chdir = self.patch(runtime.os, "chdir", AssertionError("Unexpected cwd change"))
        self.connection = mock.MagicMock()
        self.connect = self.patch(runtime.socket, "create_connection")
        self.connect.return_value = self.connection
        self.socket_timeout = self.patch(runtime.socket, "setdefaulttimeout", self.record("socket_timeout"))
        self.proxy = self.patch(runtime, "ServerProxy", AssertionError("Unexpected RPC request"))
        self.sleep = self.patch(runtime.time, "sleep", self.record("sleep"))

    def patch(self, owner, name, side_effect=None):
        return self.stack.enter_context(mock.patch.object(owner, name, side_effect=side_effect))

    def record(self, label, result=None):
        def operation(*args, **kwargs):
            self.events.append((label, args, kwargs))
            return result
        return operation

    def set_affinity(self, pid, cpus):
        self.events.append(("set_affinity", (pid, set(cpus)), {}))
        self.requested_affinity = set(cpus)

    def get_affinity(self, pid):
        self.events.append(("get_affinity", (pid,), {}))
        return self.requested_affinity if self.actual_affinity is None else self.actual_affinity

    def run_mode(self, mode):
        with mock.patch.object(runtime.sys, "argv", [str(SOURCE), mode]):
            return runtime.main()

    def assert_no_exec(self):
        self.execv.assert_not_called()
        self.execvp.assert_not_called()
        self.popen.assert_not_called()

    def test_cpu_parser_handles_ranges_and_rejects_invalid_configuration(self):
        self.assertEqual({0, 1, 2, 4, 7, 8}, runtime.cpu_set("0-2,4, 7-8,2"))
        for value in ("", "-1", "2-1", "0-1-2", "1,", ",1", "all", "1,,2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runtime.cpu_set(value)

    def test_mls_waits_for_mongo_and_portal_and_preserves_working_directory(self):
        wait = self.patch(runtime, "wait_for_ports", self.record("wait"))
        supervisor = self.patch(runtime, "start_mls", self.record("supervise", result=7))
        self.assertEqual(7, self.run_mode("start"))
        self.assertEqual(set(range(20)) - {6, 7}, self.requested_affinity)
        wait.assert_called_once_with([27018, 13000], 180)
        supervisor.assert_called_once_with({"ml": 8100, "core": 13000, "mongo": 27018})
        self.assertEqual(["set_affinity", "get_affinity", "wait", "supervise"],
                         [event[0] for event in self.events])
        self.chdir.assert_not_called()
        self.proxy.assert_not_called()

    def test_mls_affinity_failure_prevents_dependency_checks_and_exec(self):
        self.actual_affinity = {6, 7}
        wait = self.patch(runtime, "wait_for_ports")
        with self.assertRaises(RuntimeError):
            self.run_mode("start")
        wait.assert_not_called()
        self.assert_no_exec()

    def test_start_without_optional_settings_neither_pins_nor_waits(self):
        supervisor = self.patch(runtime, "start_mls", self.record("supervise", result=0))
        with mock.patch.dict(runtime.os.environ, {}, clear=True):
            self.assertEqual(0, self.run_mode("start"))
        supervisor.assert_called_once_with({"ml": 8000, "core": 12000, "mongo": 27017})
        self.affinity.assert_not_called()
        self.connect.assert_not_called()

    def test_legacy_lower_case_port_names_are_still_read(self):
        supervisor = self.patch(runtime, "start_mls", self.record("supervise", result=0))
        legacy = {"interface_port": "8200", "mios_port": "13100", "mongo_port": "27019"}
        with mock.patch.dict(runtime.os.environ, legacy, clear=True):
            self.run_mode("start")
        supervisor.assert_called_once_with({"ml": 8200, "core": 13100, "mongo": 27019})

    def test_probes_only_open_local_tcp_connections_without_rpc_or_state_changes(self):
        self.patch(runtime, "mls_pid").return_value = 91
        owned = self.patch(runtime, "check_owned_ports",
                           lambda pid, ports: runtime.check_ports(ports))
        for mode, pid, ports in (("probe", 91, [8100, 8101]),):
            with self.subTest(mode=mode):
                self.connect.reset_mock()
                self.connection.reset_mock()
                self.run_mode(mode)
                owned.assert_called_with(pid, ports)
                self.assertEqual([mock.call(("127.0.0.1", port), timeout=1) for port in ports],
                                 self.connect.call_args_list)
                self.assertEqual(len(ports), self.connection.__exit__.call_count)
                self.connection.send.assert_not_called()
                self.connection.sendall.assert_not_called()
        self.proxy.assert_not_called()
        self.affinity.assert_not_called()
        self.assert_no_exec()

    def test_probe_connection_failure_propagates_without_rpc_fallback(self):
        self.patch(runtime, "mls_pid").return_value = 91
        self.patch(runtime, "check_owned_ports", lambda pid, ports: runtime.check_ports(ports))
        self.connect.side_effect = ConnectionRefusedError("port closed")
        with self.assertRaises(ConnectionRefusedError):
            self.run_mode("probe")
        self.proxy.assert_not_called()
        self.assert_no_exec()

    def test_dependency_wait_retries_only_within_deadline(self):
        self.connect.side_effect = [ConnectionRefusedError(), self.connection]
        with mock.patch.object(runtime.time, "monotonic", side_effect=[0, 0]):
            runtime.wait_for_ports([27018], timeout=4)
        self.assertEqual(2, self.connect.call_count)
        self.sleep.assert_called_once_with(2)
        self.connect.reset_mock()
        self.sleep.reset_mock()
        self.connect.side_effect = ConnectionRefusedError()
        with mock.patch.object(runtime.time, "monotonic", side_effect=[0, 4]), \
                self.assertRaisesRegex(RuntimeError, "Dependencies.*unavailable"):
            runtime.wait_for_ports([27018], timeout=4)
        self.connect.assert_called_once()
        self.sleep.assert_not_called()
        self.proxy.assert_not_called()

    def test_stop_hook_bounds_rpc_and_calls_only_service_stop(self):
        self.patch(runtime, "mls_pid").return_value = 91
        owned = self.patch(runtime, "check_owned_ports", self.record("owned"))
        service = mock.MagicMock()
        self.proxy.side_effect = self.record("proxy", result=service)
        self.run_mode("stop")
        owned.assert_called_once_with(91, [8100])
        self.socket_timeout.assert_called_once_with(5)
        self.proxy.assert_called_once_with("http://127.0.0.1:8100/", allow_none=True)
        self.assertEqual([mock.call.stop_service()], service.__enter__.return_value.method_calls)
        service.__exit__.assert_called_once()
        self.assertEqual(["owned", "socket_timeout", "proxy"], [event[0] for event in self.events])
        self.connect.assert_not_called()
        self.assert_no_exec()

    def test_stop_hook_refuses_foreign_listener_before_rpc(self):
        self.patch(runtime, "mls_pid").return_value = 91
        self.patch(runtime, "check_owned_ports", RuntimeError("not owned"))
        with self.assertRaisesRegex(RuntimeError, "not owned"):
            self.run_mode("stop")
        self.proxy.assert_not_called()
        self.socket_timeout.assert_not_called()

    def test_stop_hook_reports_rejected_cancellation(self):
        self.patch(runtime, "mls_pid").return_value = 91
        self.patch(runtime, "check_owned_ports")
        self.proxy.side_effect = None
        service = self.proxy.return_value.__enter__.return_value
        service.stop_service.return_value = False
        with self.assertRaisesRegex(RuntimeError, "did not acknowledge"):
            self.run_mode("stop")
        service.stop_service.assert_called_once_with()
        self.assert_no_exec()

    def test_stop_hook_accepts_legacy_no_return_value(self):
        self.patch(runtime, "mls_pid").return_value = 91
        self.patch(runtime, "check_owned_ports")
        self.proxy.side_effect = None
        service = self.proxy.return_value.__enter__.return_value
        service.stop_service.return_value = None
        self.run_mode("stop")
        service.stop_service.assert_called_once_with()
        self.assert_no_exec()

    def test_mls_marker_rejects_reused_pid_foreign_parent_and_missing_file(self):
        self.marker.read_text.return_value = "91 456\n"
        identity = self.patch(runtime, "process_identity")
        identity.return_value = (1, 456)
        self.assertEqual(91, runtime.mls_pid())
        for actual in ((1, 457), (2, 456)):
            identity.return_value = actual
            with self.subTest(identity=actual), self.assertRaisesRegex(RuntimeError, "marker"):
                runtime.mls_pid()
        self.marker.read_text.side_effect = FileNotFoundError()
        with self.assertRaises(FileNotFoundError):
            runtime.mls_pid()
        self.connect.assert_not_called()
        self.proxy.assert_not_called()

    def test_process_identity_handles_spaces_in_names_and_rejects_zombies(self):
        stat = mock.Mock()
        self.paths.side_effect = None
        self.paths.return_value = stat
        fields = ["S", "1"] + ["0"] * 17 + ["456"]
        stat.read_text.return_value = "91 (python worker) " + " ".join(fields)
        self.assertEqual((1, 456), runtime.process_identity(91))
        fields[0] = "Z"
        stat.read_text.return_value = "91 (python worker) " + " ".join(fields)
        with self.assertRaisesRegex(RuntimeError, "exited"):
            runtime.process_identity(91)

    def test_owned_ports_require_this_process_listening_sockets_before_tcp_probe(self):
        fd_directory = mock.Mock()
        fd_directory.iterdir.return_value = ["fd3", "fd4", "closing-fd"]
        ipv4, ipv6 = mock.Mock(), mock.Mock()
        ipv4.exists.return_value = ipv6.exists.return_value = True
        self.paths.side_effect = lambda path: {
            "/proc/91/fd": fd_directory, "/proc/net/tcp": ipv4, "/proc/net/tcp6": ipv6,
        }[path]

        def readlink(fd):
            if fd == "closing-fd":
                raise FileNotFoundError()
            return {"fd3": "socket:[100]", "fd4": "socket:[101]"}[fd]

        self.patch(runtime.os, "readlink", readlink)

        def table(port, inode, state="0A"):
            return f"header\n0: 00000000:{port:04X} 00000000:0000 {state} 0:0 00:0 0 0 0 {inode}\n"

        ipv4.read_text.return_value = table(8100, 100)
        ipv6.read_text.return_value = table(8101, 101)
        runtime.check_owned_ports(91, [8100, 8101])
        self.assertEqual(2, self.connect.call_count)
        for inode, state in ((999, "0A"), (101, "01")):
            self.connect.reset_mock()
            ipv6.read_text.return_value = table(8101, inode, state)
            with self.subTest(inode=inode, state=state), \
                    self.assertRaisesRegex(RuntimeError, "does not own listeners"):
                runtime.check_owned_ports(91, [8100, 8101])
            self.connect.assert_not_called()
        self.proxy.assert_not_called()

    def prepare_supervisor(self):
        child = mock.Mock(pid=91)
        child.wait.return_value = 0
        child.poll.return_value = 0
        self.popen.side_effect = self.record("popen", result=child)
        self.patch(runtime, "process_identity").return_value = (1, 456)
        handlers = {}

        def install(sig, handler):
            self.events.append(("signal", (sig, handler), {}))
            handlers[sig] = handler
            return runtime.signal.SIG_DFL

        self.signals.side_effect = install
        return child, handlers

    def test_mls_supervisor_launches_child_with_current_cwd_and_cleans_marker(self):
        child, _ = self.prepare_supervisor()
        child.wait.return_value = 7
        child.poll.return_value = 7
        ports = {"ml": 8100, "core": 13000, "mongo": 27018}
        self.assertEqual(7, runtime.start_mls(ports))
        (command,), options = self.popen.call_args
        self.assertEqual(["python3", "-u", "./start_interface.py"], command)
        self.assertTrue(options["start_new_session"])
        self.assertEqual(("8100", "13000", "27018"),
                         tuple(options["env"][name] for name in ("interface_port", "mios_port", "mongo_port")))
        self.marker.write_text.assert_called_once_with("91 456\n")
        self.marker.unlink.assert_called_once_with(missing_ok=True)
        self.chdir.assert_not_called()
        self.killpg.assert_not_called()
        self.assertEqual(["signal", "signal", "popen", "signal", "signal"],
                         [event[0] for event in self.events])
        self.assertEqual([mock.call(runtime.signal.SIGTERM, runtime.signal.SIG_DFL),
                          mock.call(runtime.signal.SIGINT, runtime.signal.SIG_DFL)],
                         self.signals.call_args_list[-2:])

    def test_mls_supervisor_forwards_stop_and_kills_unresponsive_group_after_deadline(self):
        child, handlers = self.prepare_supervisor()
        child.poll.return_value = -9
        attempts = 0

        def wait(timeout):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                self.assertEqual(1, timeout)
                handlers[runtime.signal.SIGTERM](runtime.signal.SIGTERM, None)
                raise runtime.subprocess.TimeoutExpired("mls", timeout)
            self.assertEqual(2, timeout)
            return -9

        child.wait.side_effect = wait
        with mock.patch.object(runtime.time, "monotonic", side_effect=[0, 10]):
            self.assertEqual(0, runtime.start_mls({"ml": 8100, "core": 13000, "mongo": 27018}))
        self.assertEqual([mock.call(91, runtime.signal.SIGTERM),
                          mock.call(91, runtime.signal.SIGKILL)], self.killpg.call_args_list)
        self.marker.unlink.assert_called_once_with(missing_ok=True)

    def test_mls_marker_failure_still_kills_child_and_restores_signal_handlers(self):
        child, _ = self.prepare_supervisor()
        child.poll.return_value = None
        child.wait.return_value = -9
        self.marker.write_text.side_effect = PermissionError("cannot write marker")
        self.marker.unlink.side_effect = PermissionError("cannot unlink marker")
        with self.assertRaisesRegex(PermissionError, "cannot write marker"):
            runtime.start_mls({"ml": 8100, "core": 13000, "mongo": 27018})
        self.killpg.assert_called_once_with(91, runtime.signal.SIGKILL)
        child.wait.assert_called_once_with(timeout=2)
        self.assertEqual([mock.call(runtime.signal.SIGTERM, runtime.signal.SIG_DFL),
                          mock.call(runtime.signal.SIGINT, runtime.signal.SIG_DFL)],
                         self.signals.call_args_list[-2:])


if __name__ == "__main__":
    unittest.main()
