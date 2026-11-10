from utils.helper_functions import Task
from utils.ws_client import call_method
from threading import Event, Lock, Thread, current_thread


class CMDLoop:
    _RPC_TIMEOUT = 5
    _OPEN_TIMEOUT = 2
    _CLOSE_TIMEOUT = 0.2
    _DISPATCH_LOCK_TIMEOUT = 2.5
    _JOIN_TIMEOUT = 1

    def __init__(self, cmd):
        self.keep_running = False
        self.thread = None
        self.cmd = cmd
        self.agent = self.cmd["agent"]
        self.sleep = cmd.get("sleep", 0)
        self.port = cmd.get("port", 13000)
        self.skills = cmd["skills"]
        self.stop_requested = Event()
        self.finished = Event()
        self.last_error = None
        self._dispatch_lock = Lock()

    @staticmethod
    def _accepted(response):
        return (isinstance(response, dict) and isinstance(response.get("result"), dict)
                and response["result"].get("result") is True)

    def _call(self, method, payload, **kwargs):
        return call_method(
            self.agent, self.port, method, payload, timeout=self._RPC_TIMEOUT,
            open_timeout=self._OPEN_TIMEOUT, close_timeout=self._CLOSE_TIMEOUT, **kwargs)

    def _execute_loop(self):
        try:
            task = Task(self.agent, self.port)
            for i in range(100):
                if self.stop_requested.is_set():
                    return
                for skill in self.skills:
                    task.add_skill(f"{skill[0]}-{i}", skill[1], skill[2])
            while self.keep_running and not self.stop_requested.is_set():
                # An in-flight start must finish before stop clears Core's queue.
                # Never cancel this exchange merely because stop was requested;
                # its response establishes ordering when the transport succeeds.
                with self._dispatch_lock:
                    if self.stop_requested.is_set():
                        return
                    response = self._call("start_task", {
                        "task": "GenericTask", "parameters": task.context, "queue": False})
                if self.stop_requested.is_set():
                    return
                task_uuid = response["result"].get("task_uuid") if self._accepted(response) else None
                if not isinstance(task_uuid, str) or not task_uuid or task_uuid == "INVALID":
                    raise RuntimeError("CMDLoop task dispatch was rejected or unconfirmed")
                response = call_method(
                    self.agent, self.port, "wait_for_task", {"task_uuid": task_uuid},
                    timeout=1000, open_timeout=self._OPEN_TIMEOUT,
                    close_timeout=self._CLOSE_TIMEOUT, cancel_event=self.stop_requested)
                if self.stop_requested.is_set():
                    return
                if not self._accepted(response):
                    raise RuntimeError("CMDLoop task completion was not confirmed")
                if self.sleep and self.stop_requested.wait(self.sleep):
                    return
        except Exception as error:
            self.last_error = str(error)
            # A missing reply may still mean Core accepted the command. End the
            # loop and request stop instead of repeating an uncertain dispatch.
            self.stop()
        finally:
            self.keep_running = False
            self.finished.set()

    def request_stop(self):
        """Prevent more dispatch immediately, without waiting for Core or a lock."""
        self.stop_requested.set()
        self.keep_running = False

    def stop(self):
        """Return True only after Core accepts stop and the loop thread has exited."""
        self.request_stop()
        if not self._dispatch_lock.acquire(timeout=self._DISPATCH_LOCK_TIMEOUT):
            self.last_error = "CMDLoop dispatch is still pending; retry stop"
            return False
        try:
            try:
                response = self._call("stop_task", {
                    "raise_exception": False, "recover": False, "empty_queue": True})
                accepted = self._accepted(response)
                if not accepted:
                    self.last_error = "Core did not confirm CMDLoop stop; retry stop"
            except Exception as error:
                self.last_error = f"CMDLoop stop failed: {error}"
                accepted = False
        finally:
            self._dispatch_lock.release()
        thread = self.thread
        if thread is not None and thread is not current_thread():
            thread.join(timeout=self._JOIN_TIMEOUT)
        return accepted and (thread is None or not thread.is_alive())

    def start(self):
        if self.stop_requested.is_set():
            return False
        with self._dispatch_lock:
            if self.stop_requested.is_set() or self.thread is not None:
                return False
            self.keep_running = True
            self.thread = Thread(target=self._execute_loop, name="mios-cmd-loop")
            self.thread.start()
            return True
