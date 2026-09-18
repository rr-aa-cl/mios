"""Read-only alignment display tests; every possible client call is mocked."""

from copy import deepcopy
import json
import math
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

import watch_insertion_alignment as watch
from utils import ws_client


def reply(**values):
    return {"result": {"result": True, "error": "", **values}}


def rotation_x(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rotation_z(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rotation_vector_matrix(degrees):
    """Rodrigues reconstruction independent of the monitor's SciPy conversion."""
    vector = np.radians(np.asarray(degrees, dtype=float))
    angle = np.linalg.norm(vector)
    if angle == 0:
        return np.eye(3)
    x, y, z = vector / angle
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + math.sin(angle) * cross + (1 - math.cos(angle)) * (cross @ cross)


def encode(pose):
    return pose.reshape(-1, order="F").tolist()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(watch, "call_method", Mock(side_effect=AssertionError("Unexpected Core read")))
    monkeypatch.setattr(ws_client, "send", Mock(side_effect=AssertionError("Unexpected WebSocket transport")))


@pytest.fixture
def saved(tmp_path):
    container = np.eye(4)
    # Container Z points along base X. The frame also rotates both lateral axes.
    container[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    container[:3, 3] = [0.6, -0.2, 0.4]
    seated = container.copy()
    seated[:3, 3] += container[:3, :3] @ np.array([0.00005, -0.00021, -0.00011])
    seated[:3, :3] = container[:3, :3] @ rotation_x(0.96)
    raw = {
        "state": reply(status="Idle", current_task="IdleTask", control_active=False,
                       grasped_object="test-peg", O_T_EE=encode(seated), q=[0] * 7),
        "container": reply(context={"name": "test-peg_container", "O_T_OB": encode(container), "q": [0] * 7}),
    }
    path = tmp_path / "seated-reference.json"

    def write():
        path.write_text(json.dumps(raw))

    write()
    return SimpleNamespace(raw=raw, path=path, write=write, seated=seated, container=container)


def test_rotated_column_major_frame_measures_withdrawal_from_actual_seat(saved):
    reference = watch.read_reference(saved.path)
    np.testing.assert_allclose(reference["container"], saved.container)
    np.testing.assert_allclose(reference["seated"], saved.seated)
    state = deepcopy(saved.raw["state"]["result"])
    at_seat = watch.alignment(reference, state)
    np.testing.assert_allclose(at_seat["offset_mm"], [0, 0, 0], atol=1e-12)
    assert at_seat["orientation_change_deg"] == pytest.approx(0, abs=1e-6)
    # The nonzero original Container-versus-seat offset must not reappear.
    measured = saved.seated.copy()
    measured[:3, 3] += saved.container[:3, :3] @ np.array([0.0003, -0.0004, -0.030])
    state["O_T_EE"] = encode(measured)
    state.update(status="Move", current_task="GenericTask", control_active=True)
    result = watch.alignment(reference, state)
    np.testing.assert_allclose(result["offset_mm"], [0.3, -0.4, -30], atol=1e-10)
    assert result["lateral_mm"] == pytest.approx(0.5)
    assert result["orientation_change_deg"] == pytest.approx(0, abs=1e-6)
    assert result["status"] == "Move"


def test_orientation_is_relative_to_actual_seat_including_rotation_about_axis(saved):
    reference = watch.read_reference(saved.path)
    state = deepcopy(saved.raw["state"]["result"])
    measured = saved.seated.copy()
    measured[:3, :3] = saved.seated[:3, :3] @ rotation_z(1.2)
    state["O_T_EE"] = encode(measured)
    result = watch.alignment(reference, state)
    assert result["orientation_change_deg"] == pytest.approx(1.2, abs=1e-10)
    assert result["lateral_mm"] == pytest.approx(0)


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("angle", [-3.2, 1.7])
def test_orientation_correction_has_restoring_sign_in_fixed_container_axes(saved, axis, angle):
    reference = watch.read_reference(saved.path)
    state = deepcopy(saved.raw["state"]["result"])
    local_rotation = np.zeros(3)
    local_rotation[axis] = angle
    frame = saved.container[:3, :3]
    measured = saved.seated.copy()
    measured[:3, :3] = frame @ rotation_vector_matrix(local_rotation) @ frame.T @ saved.seated[:3, :3]
    state["O_T_EE"] = encode(measured)

    result = watch.alignment(reference, state)

    np.testing.assert_allclose(result["orientation_correction_deg"], -local_rotation, atol=1e-12)
    assert result["orientation_change_deg"] == pytest.approx(abs(angle), abs=1e-12)


def test_composed_rotation_correction_reconstructs_actual_seated_orientation(saved):
    reference = watch.read_reference(saved.path)
    state = deepcopy(saved.raw["state"]["result"])
    frame = saved.container[:3, :3]
    # Noncommuting rotations distinguish an axis-angle vector from Euler angles.
    local_rotation = rotation_z(31) @ rotation_x(-17)
    measured = saved.seated.copy()
    measured[:3, :3] = frame @ local_rotation @ frame.T @ saved.seated[:3, :3]
    measured[:3, 3] += frame @ [0, 0, -0.037]
    state["O_T_EE"] = encode(measured)

    result = watch.alignment(reference, state)
    correction = np.array(result["orientation_correction_deg"])
    restored = rotation_vector_matrix(frame @ correction) @ measured[:3, :3]

    np.testing.assert_allclose(restored, saved.seated[:3, :3], atol=1e-12)
    assert result["orientation_change_deg"] == pytest.approx(np.linalg.norm(correction))
    np.testing.assert_allclose(result["offset_mm"], [0, 0, -37], atol=1e-10)


@pytest.mark.parametrize("angle", [0, 0.000001, 179.999999, 180, -180])
def test_correction_is_finite_and_reconstructs_zero_small_and_half_turn_rotations(saved, angle):
    reference = watch.read_reference(saved.path)
    state = deepcopy(saved.raw["state"]["result"])
    frame = saved.container[:3, :3]
    measured = saved.seated.copy()
    measured[:3, :3] = frame @ rotation_z(angle) @ frame.T @ saved.seated[:3, :3]
    state["O_T_EE"] = encode(measured)

    result = watch.alignment(reference, state)
    correction = np.array(result["orientation_correction_deg"])

    assert np.isfinite(correction).all()
    assert result["orientation_change_deg"] == pytest.approx(abs(angle), abs=1e-9)
    # At 180 degrees either axis sign represents the same restoring rotation.
    restored = rotation_vector_matrix(frame @ correction) @ measured[:3, :3]
    np.testing.assert_allclose(restored, saved.seated[:3, :3], atol=1e-12)
    if angle == 0:
        np.testing.assert_allclose(correction, [0, 0, 0], atol=1e-12)


@pytest.mark.parametrize("problem", ["moving_reference", "active_reference", "wrong_task",
                                     "wrong_container", "missing_object", "reflection", "invalid_joints"])
def test_invalid_saved_reference_fails_before_any_core_read(saved, problem, capsys):
    state = saved.raw["state"]["result"]
    if problem == "moving_reference":
        state["status"] = "Move"
    elif problem == "active_reference":
        state["control_active"] = True
    elif problem == "wrong_task":
        state["current_task"] = "GenericTask"
    elif problem == "wrong_container":
        saved.raw["container"]["result"]["context"]["name"] = "other-peg_container"
    elif problem == "missing_object":
        state.pop("grasped_object")
    elif problem == "reflection":
        reflected = saved.seated.copy()
        reflected[:3, 0] *= -1
        state["O_T_EE"] = encode(reflected)
    else:
        state["q"][0] = float("nan")
    saved.write()
    assert watch.main(["--robot", "offline.invalid", "--reference", str(saved.path)]) == 1
    watch.call_method.assert_not_called()
    assert "Robot control is unchanged" in capsys.readouterr().err


@pytest.mark.parametrize("problem", ["wrong_object", "reflex", "fault_reply", "nonrigid_pose", "missing_pose"])
def test_bad_current_state_stops_display_after_only_a_read(saved, monkeypatch, problem, capsys):
    response = deepcopy(saved.raw["state"])
    state = response["result"]
    if problem == "wrong_object":
        state["grasped_object"] = "other-peg"
    elif problem == "reflex":
        state["status"] = "Reflex"
    elif problem == "fault_reply":
        state.update(result=False, error_message="No current state available")
    elif problem == "nonrigid_pose":
        state["O_T_EE"][1] = 2.0
    else:
        state.pop("O_T_EE")
    rpc = Mock(return_value=response)
    monkeypatch.setattr(watch, "call_method", rpc)
    assert watch.main(["--robot", "offline.invalid", "--reference", str(saved.path)]) == 1
    rpc.assert_called_once_with("offline.invalid", 12000, "get_state", {}, **watch.RPC_LIMITS)
    assert "Robot control is unchanged" in capsys.readouterr().err


def test_cli_reads_only_get_state_at_bounded_intervals_and_never_mutates_reference(saved, monkeypatch, capsys):
    now, sleeps = [0.0], []

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(watch, "time", SimpleNamespace(monotonic=lambda: now[0], sleep=sleep))
    before = saved.path.read_bytes()
    rpc = Mock(return_value=deepcopy(saved.raw["state"]))
    monkeypatch.setattr(watch, "call_method", rpc)
    assert watch.main(["--robot", "offline.invalid", "--reference", str(saved.path), "--duration", "1.1"]) == 0
    assert rpc.call_count == 3
    assert sleeps == pytest.approx([0.5, 0.5, 0.1])
    for call in rpc.call_args_list:
        assert call.args == ("offline.invalid", 12000, "get_state", {})
        assert call.kwargs == watch.RPC_LIMITS
    assert saved.path.read_bytes() == before
    ws_client.send.assert_not_called()
    output = capsys.readouterr().out
    assert "lateral 0.000 mm" in output
    assert "rot correction [" in output
    assert "Display finished. Robot control is unchanged." in output


def test_keyboard_interrupt_stops_display_without_robot_stop_request(saved, monkeypatch, capsys):
    rpc = Mock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(watch, "call_method", rpc)
    assert watch.main(["--robot", "offline.invalid", "--reference", str(saved.path)]) == 0
    rpc.assert_called_once_with("offline.invalid", 12000, "get_state", {}, **watch.RPC_LIMITS)
    assert "Display stopped. Robot control is unchanged." in capsys.readouterr().out


@pytest.mark.parametrize("duration", ["0", "-1", "nan", "inf"])
def test_invalid_duration_is_rejected_before_any_rpc(saved, duration):
    with pytest.raises(SystemExit) as error:
        watch.main(["--robot", "offline.invalid", "--reference", str(saved.path), "--duration", duration])
    assert error.value.code == 2
    watch.call_method.assert_not_called()
