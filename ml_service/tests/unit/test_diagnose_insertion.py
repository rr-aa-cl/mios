"""One-shot diagnostic contract with every external operation mocked."""

from copy import deepcopy
import json
import math
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec

import pytest

import diagnose_insertion as diagnostic
from services.base_service import BaseService
from utils import ws_client


def accepted(**values):
    return {"result": {"result": True, "error": "", **values}}


def completion(skill):
    return accepted(task_result={
        "success": True, "exception": False, "external_stop": False, "error": [],
        "skill_results": {skill: {"cost": {"time": 0.5}, "heuristic": 0.0}},
    })


@pytest.fixture
def session(monkeypatch, tmp_path):
    calls = Mock()
    mocks = {}
    for name in ("check_learning_services", "check_taught_insertion_objects", "call_method",
                 "start_task", "wait_for_task", "stop_task"):
        value = create_autospec(getattr(diagnostic, name), return_value=None)
        monkeypatch.setattr(diagnostic, name, value)
        calls.attach_mock(value, name)
        mocks[name] = value
    pose = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0.5, 0.1, 0.6, 1]
    target = {"name": "taught_object_container_approach", "O_T_OB": pose, "q": [0.0] * 7}
    state = accepted(status="Idle", current_task="IdleTask", control_active=False,
                     grasped_object="taught_object", O_T_EE=deepcopy(pose), q=[0.0] * 7)

    def rpc(robot, port, method, payload, **kw):
        if method == "get_state":
            return deepcopy(state)
        if method == "download_object_context":
            return accepted(context=deepcopy(target))
        return accepted()

    mocks["call_method"].side_effect = rpc
    mocks["start_task"].side_effect = [accepted(task_uuid="setup-uuid"), accepted(task_uuid="insertion-uuid")]
    mocks["wait_for_task"].side_effect = [completion("move"), completion("insertion")]
    mocks["stop_task"].return_value = accepted()
    output = tmp_path / "trial"
    return SimpleNamespace(
        **mocks, calls=calls, output=output, state=state, target=target, rpc=rpc,
        run=lambda **kw: diagnostic.run_diagnostic("offline.invalid", "taught_object", output, **kw),
        events=lambda: [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()],
    )


def test_default_cli_only_writes_plan_with_the_same_nominal_learning_candidate(session):
    assert diagnostic.main(["--robot", "offline.invalid", "--insertable", "taught_object",
                            "--output", str(session.output)]) == 0

    assert session.calls.mock_calls == []
    plan = json.loads((session.output / "plan.json").read_text())
    assert [task["stage"] for task in plan["tasks"]] == ["setup", "insertion"]
    assert all(task["request"]["queue"] is False for task in plan["tasks"])
    setup = plan["tasks"][0]["request"]["parameters"]["skills"]["move"]
    assert setup["control"]["control_mode"] == 1
    assert setup["skill"]["speed"] == 0.10
    pd = diagnostic.InsertionFactory(["offline.invalid"], diagnostic.TimeMetric("insertion", {"time": 15}), {
        "Insertable": "taught_object", "Container": "taught_object_container",
        "Approach": "taught_object_container_approach",
    }).get_problem_definition("taught_object")
    diagnostic.configure_supervised_motion(pd)
    physical = diagnostic.supervised_nominal_knowledge(pd)["parameters"]
    mapper = SimpleNamespace(problem_definition=pd, set_nested_parameter=lambda *a: BaseService.set_nested_parameter(None, *a))
    expected = BaseService.update_default_context(mapper, [physical[name] for name in pd.domain.vector_mapping])
    expected["parameters"]["as_queue"] = False
    assert plan["tasks"][1]["request"]["parameters"] == expected
    assert physical["p1_dx_d"] == 0.02
    approach = plan["tasks"][1]["request"]["parameters"]["skills"]["insertion"]["skill"]["p0"]
    assert approach["dX_d"] == [0.02, 0.10]
    assert approach["ddX_d"] == [0.10, 0.20]


def test_dry_run_restores_fifteen_second_budget_from_older_five_second_factory(session, monkeypatch):
    original_get = diagnostic.InsertionFactory.get_problem_definition
    source = Path(diagnostic.__file__).resolve().parents[1] / "python/taxonomy/default_contexts/insertion.json"
    original_contents = source.read_bytes()
    supplied_limits = []

    def legacy_definition(factory, *args, **kwargs):
        problem = original_get(factory, *args, **kwargs)
        skill = problem.default_context["skills"]["insertion"]["skill"]
        skill["time_max"] = 5.0
        supplied_limits.append(skill["time_max"])
        return problem

    monkeypatch.setattr(diagnostic.InsertionFactory, "get_problem_definition", legacy_definition)
    session.run()

    assert supplied_limits == [5.0]
    assert session.calls.mock_calls == []
    plan = json.loads((session.output / "plan.json").read_text())
    insertion = plan["tasks"][1]["request"]["parameters"]["skills"]["insertion"]["skill"]
    assert insertion["time_max"] == 15.0
    assert source.read_bytes() == original_contents


def test_success_dispatches_only_setup_then_insertion_and_logs_before_each_start(session):
    dispatched = []

    def start(*args, **kwargs):
        latest = session.events()[-1]
        assert latest["kind"] == "request"
        assert latest["operation"].endswith(".start_task")
        assert latest["data"]["parameters"] == kwargs["parameters"]
        dispatched.append(kwargs["parameters"]["parameters"]["skill_names"])
        return accepted(task_uuid="task-" + str(len(dispatched)))

    session.start_task.side_effect = start
    session.run(run=True)

    assert dispatched == [["move"], ["insertion"]]
    assert session.check_learning_services.call_count == 4
    order = [call[0] for call in session.calls.mock_calls]
    assert order.index("check_learning_services") < order.index("stop_task")
    assert order.index("check_taught_insertion_objects") < order.index("stop_task")
    starts = [index for index, name in enumerate(order) if name == "start_task"]
    assert "check_learning_services" in order[starts[0] + 1:starts[1]]
    assert session.stop_task.call_count == 2
    for call in session.stop_task.call_args_list:
        assert call.kwargs["recover"] is False and call.kwargs["empty_queue"] is True
    for call in session.start_task.call_args_list:
        assert call.kwargs["queue"] is False and call.kwargs["timeout"] == 5
    for call in session.wait_for_task.call_args_list:
        assert call.kwargs["timeout"] == 50 and call.kwargs["close_timeout"] == 0.2
    for call in session.call_method.call_args_list:
        assert call.kwargs["timeout"] == 5
    assert session.events()[-1]["kind"] == "completed"


@pytest.mark.parametrize("change", [
    {"success": False}, {"success": 1}, {"exception": True}, {"external_stop": True},
    {"error": ["ControllerActivationFailed"]}, {"skill_results": {}},
    {"skill_results": {"move": {"cost": {}, "heuristic": 0, "success": "true"}}},
    {"skill_results": {"move": {"cost": {}, "heuristic": 0, "errors": ["Guard"]}}},
])
def test_failed_or_ambiguous_setup_never_dispatches_insertion(session, change):
    response = completion("move")
    response["result"]["task_result"].update(change)
    session.wait_for_task.side_effect = [response]

    with pytest.raises(RuntimeError):
        session.run(run=True)

    session.start_task.assert_called_once()
    session.wait_for_task.assert_called_once()
    assert session.stop_task.call_count == 2
    assert not any(event["kind"] == "completed" for event in session.events())


def test_insertion_failure_has_no_reset_rescue_or_retry(session):
    failed = completion("insertion")
    failed["result"]["task_result"]["success"] = False
    failed["result"]["task_result"]["error"] = ["tau_j_range"]
    session.wait_for_task.side_effect = [completion("move"), failed]

    with pytest.raises(RuntimeError, match="tau_j_range"):
        session.run(run=True)

    assert session.start_task.call_count == 2
    assert session.wait_for_task.call_count == 2
    assert session.stop_task.call_count == 2
    assert session.events()[-1]["operation"] == "after.state"


@pytest.mark.parametrize("reply", [None, {}, accepted(), accepted(task_uuid="INVALID"), TimeoutError("reply lost")])
def test_lost_or_malformed_start_reply_still_clears_core_queue(session, reply):
    session.start_task.side_effect = [reply]

    with pytest.raises((RuntimeError, TimeoutError)):
        session.run(run=True)

    session.start_task.assert_called_once()
    session.wait_for_task.assert_not_called()
    assert session.stop_task.call_count == 2


def test_keyboard_interrupt_while_waiting_preserves_interrupt_and_stops(session):
    interrupt = KeyboardInterrupt()
    session.wait_for_task.side_effect = interrupt

    with pytest.raises(KeyboardInterrupt) as caught:
        session.run(run=True)

    assert caught.value is interrupt
    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2


def test_reused_output_is_rejected_before_any_rpc(session):
    session.output.mkdir()

    with pytest.raises(FileExistsError):
        session.run(run=True)

    assert session.calls.mock_calls == []


def test_failed_preflight_cannot_change_object_or_dispatch_or_stop(session):
    session.check_taught_insertion_objects.side_effect = RuntimeError("Taught object missing")

    with pytest.raises(RuntimeError, match="Taught object missing"):
        session.run(run=True)

    session.start_task.assert_not_called()
    session.stop_task.assert_not_called()
    assert all(call.args[2] == "get_state" for call in session.call_method.call_args_list)


def test_unconfirmed_initial_queue_clear_prevents_all_motion(session):
    session.stop_task.side_effect = [None, accepted()]

    with pytest.raises(RuntimeError, match="Core stop"):
        session.run(run=True)

    session.start_task.assert_not_called()
    assert all(call.args[2] in ("get_state", "download_object_context")
               for call in session.call_method.call_args_list)
    assert session.stop_task.call_count == 2


def test_rejected_object_parameter_application_can_use_verified_readback(session):
    session.call_method.side_effect = lambda robot, port, method, payload, **kw: (
        {"result": {"result": False, "error": "parameter application disabled"}}
        if method == "set_grasped_object" else session.rpc(robot, port, method, payload, **kw))

    session.run(run=True)

    assert session.start_task.call_count == 2
    assert any(event["operation"] == "grasped_object.readback" for event in session.events())


def test_cleanup_failure_does_not_mask_original_failure_and_is_visible(session, capsys):
    original = RuntimeError("Original insertion failure")
    session.wait_for_task.side_effect = original
    session.stop_task.side_effect = [accepted(), None]

    with pytest.raises(RuntimeError) as caught:
        session.run(run=True)

    assert caught.value is original
    assert "Core stop unconfirmed" in capsys.readouterr().err
    assert any(event["operation"] == "cleanup" for event in session.events())


def test_log_failure_after_dispatch_cannot_prevent_final_stop(session, monkeypatch):
    original_write = diagnostic.RunLog.write

    def write(log, operation, kind, data):
        if operation == "finally.stop_task" or (operation == "setup.start_task" and kind == "response"):
            raise OSError("Output storage full")
        return original_write(log, operation, kind, data)

    monkeypatch.setattr(diagnostic.RunLog, "write", write)
    with pytest.raises(OSError, match="Output storage full"):
        session.run(run=True)

    session.start_task.assert_called_once()
    session.wait_for_task.assert_not_called()
    assert session.stop_task.call_count == 2


def test_postflight_must_confirm_readiness_even_after_accepted_stop(session):
    session.check_learning_services.side_effect = [None, None, None, RuntimeError("Core still active")]

    with pytest.raises(RuntimeError, match="Core still active"):
        session.run(run=True)

    assert session.stop_task.call_count == 2
    assert not any(event["kind"] == "completed" for event in session.events())


def legacy_transport_functions(invocations):
    """Use the remote legacy signatures, rather than permissive mocks."""
    def unexpected(name):
        invocations.append(name)
        raise AssertionError("Transport compatibility checking must never invoke " + name)

    def call_method(hostname, port, method, payload=None, endpoint="mios/core", timeout=100, silent=False):
        unexpected("call_method")

    def start_task(hostname, task, parameters=None, queue=False, port=12000):
        unexpected("start_task")

    def stop_task(hostname, raise_exception=False, recover=False, empty_queue=False, port=12000):
        unexpected("stop_task")

    def wait_for_task(hostname, task_uuid, port=12000, timeout=100):
        unexpected("wait_for_task")

    async def send(hostname, port=12000, endpoint="mios/core", request=None, timeout=100, silent=False):
        unexpected("send")

    return {"call_method": call_method, "start_task": start_task, "stop_task": stop_task,
            "wait_for_task": wait_for_task, "send": send}


@pytest.mark.parametrize("helper", ["call_method", "start_task", "stop_task", "wait_for_task", "send"])
@pytest.mark.parametrize("run", [False, True], ids=["dry_run", "physical_run_requested"])
def test_legacy_transport_is_rejected_before_planning_output_or_rpc(session, monkeypatch, capsys, helper, run):
    invocations = []
    legacy = legacy_transport_functions(invocations)[helper]
    monkeypatch.setattr(ws_client if helper == "send" else diagnostic, helper, legacy)
    build = Mock(side_effect=AssertionError("Incompatible transport must be rejected before building the plan"))
    monkeypatch.setattr(diagnostic, "build_plan", build)

    with pytest.raises(RuntimeError, match="Incompatible WebSocket client") as caught:
        session.run(run=run)

    assert "utils/ws_client.py" in str(caught.value)
    assert "No Core or MLS calls were made." in str(caught.value)
    assert invocations == []
    assert session.calls.mock_calls == []
    build.assert_not_called()
    assert not session.output.exists()
    assert "Core stop unconfirmed" not in capsys.readouterr().err


@pytest.mark.parametrize("operation", ["call_method", "start_task", "stop_task", "wait_for_task"])
def test_real_rpc_wrappers_forward_bounded_timeouts_and_exact_wire_payload(monkeypatch, operation):
    response = accepted(task_uuid="test-task")
    transport = create_autospec(ws_client.send, return_value=response)
    monkeypatch.setattr(ws_client, "send", transport)
    limits = {"timeout": 5, "open_timeout": 2, "close_timeout": 0.2}
    cancel = None
    if operation == "call_method":
        payload = {}
        method = "get_state"
        result = ws_client.call_method("offline.invalid", 12345, method, payload, **limits)
    elif operation == "start_task":
        context = {"parameters": {"skill_names": ["move"], "as_queue": False}, "skills": {"move": {}}}
        payload = {"task": "GenericTask", "parameters": context, "queue": False}
        method = "start_task"
        result = ws_client.start_task("offline.invalid", "GenericTask", parameters=context,
                                      queue=False, port=12345, **limits)
    elif operation == "stop_task":
        payload = {"raise_exception": False, "recover": False, "empty_queue": True}
        method = "stop_task"
        result = ws_client.stop_task("offline.invalid", port=12345, **payload, **limits)
    else:
        payload = {"task_uuid": "test-task"}
        method = "wait_for_task"
        cancel = Event()
        result = ws_client.wait_for_task("offline.invalid", "test-task", port=12345,
                                         cancel_event=cancel, **limits)

    assert result is response
    transport.assert_awaited_once_with(
        "offline.invalid", request={"method": method, "request": payload},
        port=12345, endpoint="mios/core", silent=False, cancel_event=cancel, **limits)


def unsuccessful_completion(skill):
    response = completion(skill)
    result = response["result"]["task_result"]
    result["success"] = False
    result["skill_results"][skill]["cost"].update(time=5.0, contact_forces=0.0, effort_total=0.0)
    return response


def run_cli(session):
    return diagnostic.main(["--robot", "offline.invalid", "--insertable", "taught_object",
                            "--output", str(session.output), "--run"])


def test_cli_reports_valid_unsuccessful_insertion_after_cleanup_and_preserves_raw_result(session, capsys):
    failed = unsuccessful_completion("insertion")
    session.wait_for_task.side_effect = [completion("move"), failed]

    assert run_cli(session) == 1

    assert session.start_task.call_count == 2
    assert session.wait_for_task.call_count == 2
    assert session.stop_task.call_count == 2
    assert [call.kwargs["parameters"]["parameters"]["skill_names"]
            for call in session.start_task.call_args_list] == [["move"], ["insertion"]]
    events = session.events()
    recorded = [event for event in events
                if event["operation"] == "insertion.wait_for_task" and event["kind"] == "response"]
    assert len(recorded) == 1 and recorded[0]["data"] == failed
    assert any(event["operation"] == "finally.stop_task" and event["kind"] == "response" for event in events)
    assert not any(event["kind"] == "completed" for event in events)
    printed = capsys.readouterr()
    summary = printed.out + printed.err
    assert "unsuccessful" in summary.lower()
    assert "success=False" in summary
    assert "insertion" in summary and str(session.output) in summary
    assert "Diagnostic completed" not in summary
    assert "Traceback" not in summary


@pytest.mark.parametrize("change", [
    {"success": "false"}, {"success": 0}, {"exception": True},
    {"error": ["ControllerActivationFailed"]}, {"skill_results": {}},
    {"skill_results": {"insertion": {"cost": {}, "heuristic": "0"}}},
    {"skill_results": {"insertion": {"cost": {}, "heuristic": 0, "errors": ["Guard"]}}},
])
def test_malformed_or_faulted_failure_is_not_classified_as_normal_unsuccessful_trial(session, capsys, change):
    failed = unsuccessful_completion("insertion")
    failed["result"]["task_result"].update(change)
    session.wait_for_task.side_effect = [completion("move"), failed]

    with pytest.raises(RuntimeError) as caught:
        run_cli(session)

    assert not isinstance(caught.value, diagnostic.TrialUnsuccessful)
    assert session.start_task.call_count == 2
    assert session.stop_task.call_count == 2
    assert not any(event["kind"] == "completed" for event in session.events())
    printed = capsys.readouterr()
    assert "unsuccessful" not in (printed.out + printed.err).lower()


def test_normal_unsuccessful_setup_is_reported_without_starting_insertion(session, capsys):
    session.wait_for_task.side_effect = [unsuccessful_completion("move")]

    assert run_cli(session) == 1

    session.start_task.assert_called_once()
    session.wait_for_task.assert_called_once()
    assert session.stop_task.call_count == 2
    printed = capsys.readouterr()
    assert "move" in printed.out + printed.err
    assert not any(event["operation"] == "insertion.start_task" for event in session.events())


def test_unsuccessful_cli_result_does_not_hide_unconfirmed_cleanup(session, capsys):
    session.wait_for_task.side_effect = [completion("move"), unsuccessful_completion("insertion")]
    session.stop_task.side_effect = [accepted(), None]

    assert run_cli(session) == 1

    assert session.start_task.call_count == 2
    assert session.stop_task.call_count == 2
    printed = capsys.readouterr()
    assert "Core stop unconfirmed" in printed.err
    assert "unsuccessful" in (printed.out + printed.err).lower()
    assert str(session.output) in printed.out + printed.err
    assert any(event["operation"] == "cleanup" and event["kind"] == "error" for event in session.events())


def test_successful_cli_returns_zero_and_reports_completion(session, capsys):
    assert run_cli(session) == 0

    assert session.start_task.call_count == 2
    assert session.stop_task.call_count == 2
    assert "Diagnostic completed" in capsys.readouterr().out
    assert session.events()[-1]["kind"] == "completed"


def arrival_result(session):
    return next(event["data"] for event in session.events()
                if event["operation"] == "setup.arrival_check" and event["kind"] == "result")


def test_arrival_target_is_saved_before_motion_and_agreement_allows_insertion(session):
    def start(*args, **kwargs):
        assert json.loads((session.output / "setup-target.json").read_text()) == session.target
        if session.start_task.call_count == 2:
            assert arrival_result(session)["passed"] is True
        return accepted(task_uuid="task-" + str(session.start_task.call_count))

    session.start_task.side_effect = start
    session.run(run=True)

    plan = json.loads((session.output / "plan.json").read_text())
    assert plan["setup_arrival_tolerances"] == {
        "position_m": 0.005, "orientation_rad": 0.0175, "joint_rad": 0.0175,
    }
    report = arrival_result(session)
    assert report["position_error_m"] == pytest.approx(0)
    assert report["orientation_error_rad"] == pytest.approx(0)
    assert report["max_joint_error_rad"] == pytest.approx(0)
    assert session.start_task.call_count == 2


def test_reported_success_with_observed_setup_pose_error_blocks_insertion(session):
    # September 17 snapshot and the supplied Approach pose, both column-major.
    session.target["q"] = [
        1.8719964027404785, -.534878134727478, -1.123138189315796, -2.015756368637085,
        .9914997220039368, 4.032334804534912, -.560555636882782,
    ]
    session.state["result"]["q"] = [
        1.8714560270309448, -.5353015065193176, -1.1218516826629639, -2.0605905055999756,
        .9873491525650024, 4.028470039367676, -.5540145635604858,
    ]
    session.target["O_T_OB"] = [
        .036084677657865605, -.03173555170382581, .9988447080484443, 0,
        .013024571515972595, -.999395817784833, -.032223592770060996, 0,
        .9992638573345648, .014172302291413712, -.03564953397461945, 0,
        .5947741866111755, .09649787098169327, .6385801434516907, 1,
    ]
    session.state["result"]["O_T_EE"] = [
        .061223385339891245, -.006464593170091092, .9981031540490533, 0,
        .03792554645790447, -.9992418339139768, -.008798311321012253, 0,
        .9974033035905747, .03839226994301501, -.060931794616851054, 0,
        .5908772945404053, .10779151320457458, .6204778552055359, 1,
    ]

    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    report = arrival_result(session)
    assert report["passed"] is False
    assert report["position_error_m"] == pytest.approx(.021689282196895164)
    assert math.degrees(report["orientation_error_rad"]) == pytest.approx(2.454298086)
    assert report["max_joint_error_rad"] == pytest.approx(.044834136962890625)
    assert report["joint_errors_rad"][3] == report["max_joint_error_rad"]
    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2
    assert any(event["operation"] == "finally.stop_task" for event in session.events())
    assert not any(event["operation"] == "insertion.start_task" for event in session.events())


@pytest.mark.parametrize("kind", ["position", "orientation", "joint", "joint_full_turn"])
def test_each_arrival_error_independently_prevents_insertion(session, kind):
    state = session.state["result"]
    if kind == "position":
        state["O_T_EE"][12] += .006
    elif kind == "orientation":
        c, s = math.cos(.03), math.sin(.03)
        state["O_T_EE"][:12] = [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0]
    else:
        state["q"][3] += 2 * math.pi if kind == "joint_full_turn" else .03

    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    assert arrival_result(session)["passed"] is False
    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2


@pytest.mark.parametrize("change", [
    {"q": None}, {"q": [0] * 6}, {"q": [True] * 7}, {"O_T_EE": None},
    {"O_T_EE": [0] * 16}, {"status": "Reflex"}, {"current_task": "GenericTask"},
    {"control_active": True}, {"control_active": 0}, {"result": False},
])
def test_invalid_required_setup_state_is_not_swallowed(session, change):
    def rpc(robot, port, method, payload, **kwargs):
        response = session.rpc(robot, port, method, payload, **kwargs)
        if method == "get_state" and session.start_task.call_count == 1:
            response["result"].update(change)
        return response

    session.call_method.side_effect = rpc
    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    assert arrival_result(session)["passed"] is False
    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2


@pytest.mark.parametrize("reply", [None, TimeoutError("Core state response lost")])
def test_lost_setup_state_prevents_insertion_and_clears_queue(session, reply):
    def rpc(robot, port, method, payload, **kwargs):
        if method == "get_state" and session.start_task.call_count == 1:
            if isinstance(reply, Exception):
                raise reply
            return reply
        return session.rpc(robot, port, method, payload, **kwargs)

    session.call_method.side_effect = rpc
    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2


@pytest.mark.parametrize("field,value", [
    ("q", None), ("q", [0] * 6), ("O_T_OB", [0] * 16), ("name", "different_approach"),
])
def test_invalid_target_stops_before_any_motion_or_mutation(session, field, value):
    session.target[field] = value
    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    session.start_task.assert_not_called()
    session.stop_task.assert_not_called()
    assert all(call.args[2] in ("get_state", "download_object_context")
               for call in session.call_method.call_args_list)


def test_nonzero_joint_offset_cannot_be_compared_to_unshifted_cartesian_target(session, monkeypatch):
    build = diagnostic.build_plan

    def offset_plan(*args, **kwargs):
        plan = build(*args, **kwargs)
        plan["tasks"][0]["request"]["parameters"]["skills"]["move"]["skill"]["q_g_offset"] = [.1] + [0] * 6
        return plan

    monkeypatch.setattr(diagnostic, "build_plan", offset_plan)
    with pytest.raises(diagnostic.SetupArrivalError):
        session.run(run=True)

    session.start_task.assert_not_called()
    session.stop_task.assert_not_called()


def test_cli_reports_setup_arrival_failure_with_saved_evidence(session, capsys):
    session.state["result"]["q"][0] = .1

    assert run_cli(session) == 1

    session.start_task.assert_called_once()
    assert session.stop_task.call_count == 2
    output = capsys.readouterr()
    text = output.out + output.err
    assert "setup" in text.lower()
    assert str(session.output) in text
    assert "Traceback" not in text
    assert "Diagnostic completed" not in text


@pytest.mark.parametrize("field,value", [
    ("q", [float("nan")] + [0] * 6), ("q", [float("inf")] + [0] * 6),
    ("O_T_EE", [float("nan")] + [0] * 15),
    ("O_T_EE", [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, .5, .1, .6, 1]),
])
def test_arrival_validation_rejects_nonfinite_or_reflected_feedback(session, field, value):
    # Exercise validation even when an event logger accepts non-finite values.
    session.state["result"][field] = value
    log = Mock()
    with pytest.raises(diagnostic.SetupArrivalError):
        diagnostic.require_setup_arrival("offline.invalid", log, session.target,
                                         {"position_m": .005, "orientation_rad": .0175, "joint_rad": .0175})
    report = next(call.args[2] for call in log.write.call_args_list
                  if call.args[:2] == ("setup.arrival_check", "result"))
    assert report["passed"] is False
    session.start_task.assert_not_called()
