"""Search-profile geometry and dispatch safeguards, with every external call mocked."""

from copy import deepcopy
import csv
import json
import math
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec

import numpy as np
import pytest

import diagnose_insertion as diagnostic


OVERRIDES = {"p2_wiggle_f_x": 0.3, "p2_wiggle_f_y": 0.15,
             "p2_wiggle_phi_x": 0.0, "p2_wiggle_phi_y": 0.0}


def p2(plan):
    return plan["tasks"][1]["request"]["parameters"]["skills"]["insertion"]["skill"]["p2"]


def accepted(**values):
    return {"result": {"result": True, "error": "", **values}}


def completion(skill):
    return accepted(task_result={
        "success": True, "exception": False, "external_stop": False, "error": [],
        "skill_results": {skill: {"cost": {"time": 1}, "heuristic": 0}},
    })


@pytest.fixture
def session(monkeypatch, tmp_path):
    calls, mocks = Mock(), {}
    for name in ("check_learning_services", "check_taught_insertion_objects", "call_method",
                 "start_task", "wait_for_task", "stop_task"):
        mocks[name] = create_autospec(getattr(diagnostic, name), return_value=None)
        monkeypatch.setattr(diagnostic, name, mocks[name])
        calls.attach_mock(mocks[name], name)
    pose = np.eye(4)
    pose[:3, 3] = [0.5, 0.1, 0.4]
    target = {"name": "test-peg_container_approach",
              "O_T_OB": pose.reshape(-1, order="F").tolist(), "q": [0.0] * 7}
    state = accepted(status="Idle", current_task="IdleTask", control_active=False,
                     grasped_object="test-peg", O_T_EE=deepcopy(target["O_T_OB"]), q=[0.0] * 7)

    def rpc(robot, port, method, payload, **kwargs):
        if method == "get_state":
            return deepcopy(state)
        if method == "download_object_context":
            assert payload == {"object": target["name"]}
            return accepted(context=deepcopy(target))
        if method == "set_grasped_object":
            return accepted()
        raise AssertionError(f"Unexpected Core method: {method}")

    mocks["call_method"].side_effect = rpc
    mocks["start_task"].side_effect = [accepted(task_uuid="setup"), accepted(task_uuid="insertion")]
    mocks["wait_for_task"].side_effect = [completion("move"), completion("insertion")]
    mocks["stop_task"].return_value = accepted()
    output = tmp_path / "recorded-attempt"
    return SimpleNamespace(
        **mocks, calls=calls, output=output, state=state,
        run=lambda **kwargs: diagnostic.run_diagnostic("offline.invalid", "test-peg", output, **kwargs),
        events=lambda: [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()],
    )


def test_profile_changes_only_four_mapped_search_parameters_and_keeps_original_seed():
    default = diagnostic.build_plan("offline.invalid", "test-peg")
    nominal = diagnostic.build_plan("offline.invalid", "test-peg", search_profile="nominal")
    centered = diagnostic.build_plan("offline.invalid", "test-peg", search_profile="centered-xy")

    assert default == nominal
    assert nominal["search_profile"] == "nominal"
    assert nominal["parameter_overrides"] == {}
    expected = deepcopy(nominal)
    expected["search_profile"] = "centered-xy"
    expected["parameter_overrides"] = OVERRIDES
    p2(expected)["search_f"][:2] = [0.3, 0.15]
    p2(expected)["search_phi"][:2] = [0.0, 0.0]
    # Whole-plan equality also protects setup, push, amplitudes, rotation,
    # stiffness, approach/contact motion, safety limits, and the nominal seed.
    assert centered == expected


def test_centered_waveform_has_two_independent_axes_and_zero_mean_over_its_period():
    parameters = p2(diagnostic.build_plan("offline.invalid", "test-peg", search_profile="centered-xy"))
    landmarks = diagnostic.search_waveform(parameters, [0, 5 / 6, 5 / 3, 2.5, 10 / 3, 5, 20 / 3])
    np.testing.assert_allclose(landmarks[0], np.zeros(6), atol=1e-14)
    np.testing.assert_allclose(landmarks[:, :2], [
        [0, 0], [1, math.sqrt(0.5)], [0, 1], [-1, math.sqrt(0.5)],
        [0, 0], [0, -1], [0, 0],
    ], atol=1e-14)
    # Sample one complete common period without counting its endpoint twice.
    times = np.linspace(0, 20 / 3, 2000, endpoint=False)
    wrench = diagnostic.search_waveform(parameters, times)
    assert wrench.shape == (2000, 6)
    np.testing.assert_allclose(wrench[:, :2].mean(axis=0), [0, 0], atol=1e-14)
    assert np.linalg.matrix_rank(wrench[:, :2]) == 2
    assert np.max(np.abs(wrench[:, :2])) <= 1 + 1e-14
    np.testing.assert_allclose(wrench[:, [2, 5]], 0, atol=1e-14)
    # Rotational search remains the original waveform; only X/Y change.
    nominal = p2(diagnostic.build_plan("offline.invalid", "test-peg"))
    np.testing.assert_allclose(wrench[:, 3:], diagnostic.search_waveform(nominal, times)[:, 3:])


def test_nominal_waveform_is_diagonal_and_contains_the_cpp_initial_value_offset():
    parameters = p2(diagnostic.build_plan("offline.invalid", "test-peg"))
    times = np.linspace(0, 20 / 3, 2000, endpoint=False)
    wrench = diagnostic.search_waveform(parameters, times)
    np.testing.assert_allclose(wrench[0], 0, atol=1e-14)
    np.testing.assert_allclose(wrench[:, 0], wrench[:, 1], atol=1e-14)
    assert np.linalg.matrix_rank(wrench[:, :2]) == 1
    np.testing.assert_allclose(wrench[:, :2].mean(axis=0), -math.sin(0.628), atol=1e-14)
    assert wrench[:, 0].min() == pytest.approx(-1 - math.sin(0.628), abs=1e-5)
    assert wrench[:, 0].max() == pytest.approx(1 - math.sin(0.628), abs=1e-5)


def test_centered_cli_preview_is_offline_and_records_selected_profile(session):
    assert diagnostic.main([
        "--robot", "offline.invalid", "--insertable", "test-peg", "--output", str(session.output),
        "--search-profile", "centered-xy",
    ]) == 0
    assert session.calls.mock_calls == []
    plan = json.loads((session.output / "plan.json").read_text())
    assert plan["search_profile"] == "centered-xy"
    assert plan["parameter_overrides"] == OVERRIDES
    assert (session.output / "search-preview.json").is_file()
    assert (session.output / "search-preview.csv").is_file()
    assert not (session.output / "setup-target.json").exists()


@pytest.mark.parametrize("profile", ["nominal", "centered-xy"])
def test_preview_files_use_exact_plan_and_separate_search_from_push(tmp_path, profile):
    plan = diagnostic.build_plan("offline.invalid", "test-peg", search_profile=profile)
    # A custom saved-plan value must not silently revert to the named profile.
    p2(plan)["search_a"][0] = 0.75
    diagnostic.write_search_preview(tmp_path, plan)
    report = json.loads((tmp_path / "search-preview.json").read_text())
    with (tmp_path / "search-preview.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ["time_s", "Fx_N", "Fy_N", "Fz_N", "Tx_Nm", "Ty_Nm", "Tz_Nm"]
        rows = [{key: float(value) for key, value in row.items()} for row in reader]
    assert len(rows) == 1501
    times = np.array([row["time_s"] for row in rows])
    assert times[0] == 0 and times[-1] == 15
    np.testing.assert_allclose(np.diff(times), 0.01, atol=1e-14)
    values = np.array([[row[key] for key in ("Fx_N", "Fy_N", "Fz_N", "Tx_Nm", "Ty_Nm", "Tz_Nm")]
                       for row in rows])
    np.testing.assert_allclose(values, diagnostic.search_waveform(p2(plan), times))
    assert report["search_profile"] == profile
    assert report["preview_duration_s"] == 15
    assert report["sample_interval_s"] == 0.01
    assert report["configured_f_push"] == [0, 0, 2, 0, 0, 0]
    assert np.all(values[:, 2] == 0)  # The preview must not add the separate 2 N push.
    x_axis = report["axes"][0]
    assert x_axis["amplitude"] == 0.75
    expected_mean = 0 if profile == "centered-xy" else -0.75 * math.sin(0.628)
    assert x_axis["full_cycle_mean"] == pytest.approx(expected_mean)
    assert x_axis["range"] == pytest.approx([expected_mean - 0.75, expected_mean + 0.75])


def test_unknown_profile_is_rejected_before_any_rpc_or_output(session):
    with pytest.raises(ValueError, match="profile"):
        session.run(run=True, search_profile="unknown")
    assert session.calls.mock_calls == []
    assert not session.output.exists()


def test_saved_centered_plan_matches_dispatch_and_preview_precedes_first_rpc(session):
    def ready(*args):
        assert (session.output / "search-preview.json").is_file()
        assert (session.output / "search-preview.csv").is_file()

    session.check_learning_services.side_effect = ready
    session.run(run=True, search_profile="centered-xy")
    plan = json.loads((session.output / "plan.json").read_text())
    assert session.start_task.call_count == 2
    for dispatched, saved in zip(session.start_task.call_args_list, plan["tasks"]):
        assert {key: dispatched.kwargs[key] for key in ("task", "parameters", "queue")} == saved["request"]
    checks = [event for event in session.events() if event["operation"] == "setup.arrival_check"]
    assert len(checks) == 1 and checks[0]["data"]["passed"] is True
    assert session.stop_task.call_count == 2
    assert session.stop_task.call_args.kwargs["empty_queue"] is True
    assert session.stop_task.call_args.kwargs["recover"] is False


def test_centered_profile_still_blocks_insertion_if_measured_setup_misses_target(session):
    session.state["result"]["O_T_EE"][12] += 0.0217
    with pytest.raises(diagnostic.SetupArrivalError, match="21.700 mm"):
        session.run(run=True, search_profile="centered-xy")
    session.start_task.assert_called_once()
    session.wait_for_task.assert_called_once()
    assert session.stop_task.call_count == 2
    check = next(event for event in session.events() if event["operation"] == "setup.arrival_check")
    assert check["data"]["passed"] is False


def test_preview_write_failure_prevents_every_rpc(session, monkeypatch):
    monkeypatch.setattr(diagnostic, "write_search_preview", Mock(side_effect=OSError("Preview disk full")))
    with pytest.raises(OSError, match="Preview disk full"):
        session.run(run=True, search_profile="centered-xy")
    assert session.calls.mock_calls == []
