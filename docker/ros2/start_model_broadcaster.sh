#!/usr/bin/env bash
set -euo pipefail

# Prepare arm controllers without claiming their command interfaces, then make
# Franka's read-only model available before the ROS-owned Core opens its Portal.
controller_manager="${MIOS_CONTROLLER_MANAGER:-/controller_manager}"
controller="${MIOS_MODEL_BROADCASTER:-mios_robot_model_broadcaster}"
if [[ "${controller}" == mios_effort_controller || "${controller}" == mios_joint_position_controller ]]; then
  echo "MIOS_MODEL_BROADCASTER cannot name an arm command controller." >&2
  exit 1
fi
wait_seconds="${MIOS_CONTROLLER_WAIT_SECONDS:-60}"
if [[ ! "${wait_seconds}" =~ ^[1-9][0-9]*$ ]]; then
  echo "MIOS_CONTROLLER_WAIT_SECONDS must be a positive integer." >&2
  exit 1
fi
deadline=$((SECONDS + wait_seconds))
declare -A states types

fail() {
  echo "$*" >&2
  exit 1
}

run_ros() {
  local remaining=$((deadline - SECONDS))
  (( remaining > 0 )) || { echo "Controller preparation deadline expired." >&2; return 1; }
  (( remaining <= 10 )) || remaining=10
  timeout --foreground --signal=TERM --kill-after=1 "${remaining}s" ros2 "$@"
}

inspect_controllers() {
  local line name type state extra
  states=()
  types=()
  # ros2controlcli may color lifecycle states even when its output is captured.
  while IFS= read -r line; do
    # A newly started manager can answer before any launch spawner has loaded.
    [[ "${line}" != "No controllers are currently loaded!" ]] || continue
    read -r name type state extra <<< "${line}"
    [[ -n "${name}" ]] || continue
    [[ "${name}" != \[* ]] || continue  # ROS logging, not a controller row.
    if [[ -n "${extra}" || -z "${type}" || ! "${state}" =~ ^(unconfigured|inactive|active)$ ]]; then
      fail "Cannot interpret controller state: ${name} ${type} ${state} ${extra}"
    fi
    [[ -z "${states[${name}]:-}" ]] || fail "Duplicate controller state for ${name}."
    states["${name}"]="${state}"
    types["${name}"]="${type}"
    if [[ "${state}" == active ]]; then
      case "${type}" in
        joint_state_broadcaster/JointStateBroadcaster|franka_robot_state_broadcaster/FrankaRobotStateBroadcaster|mios_ros2_control/MiosRobotModelBroadcaster) ;;
        *) fail "Refusing preparation: active command controller ${name} (${type})." ;;
      esac
    fi
  done < <(sed $'s/\033\\[[0-9;]*[mK]//g' <<< "${listing}")

  for name in "${controller}" mios_effort_controller mios_joint_position_controller; do
    case "${name}" in
      mios_effort_controller) type=mios_ros2_control/MiosEffortController ;;
      mios_joint_position_controller) type=mios_ros2_control/MiosJointPositionController ;;
      *) type=mios_ros2_control/MiosRobotModelBroadcaster ;;
    esac
    if [[ -n "${states[${name}]:-}" && "${types[${name}]}" != "${type}" ]]; then
      fail "${name} has unexpected type ${types[${name}]}; expected ${type}."
    fi
  done
}

refresh_controllers() {
  listing="$(run_ros control list_controllers -c "${controller_manager}")" \
    || fail "Cannot read controller states from ${controller_manager}."
  inspect_controllers
}

# Check every existing controller before the first load/configure/activate call.
while ! listing="$(run_ros control list_controllers -c "${controller_manager}" 2>/dev/null)"; do
  if (( SECONDS >= deadline )); then
    fail "Timed out waiting for ${controller_manager}."
  fi
  sleep 1
done
inspect_controllers

prepare_inactive() {
  local name="$1"
  if [[ -z "${states[${name}]:-}" ]]; then
    run_ros control load_controller "${name}" -c "${controller_manager}" \
      || fail "Failed to load ${name}."
    refresh_controllers
  fi
  if [[ "${states[${name}]:-}" == unconfigured ]]; then
    # Call configure directly: set_controller_state inactive could deactivate an
    # arm controller if another process activated it after our last inspection.
    run_ros service call "${controller_manager%/}/configure_controller" \
      controller_manager_msgs/srv/ConfigureController "{name: '${name}'}" \
      || fail "Failed to configure ${name}."
    refresh_controllers
  fi
  if [[ "${states[${name}]:-}" != inactive ]]; then
    fail "${name} is ${states[${name}]:-missing}, expected inactive."
  fi
}

prepare_inactive mios_effort_controller
prepare_inactive mios_joint_position_controller

if [[ "${states[${controller}]:-}" != active ]]; then
  prepare_inactive "${controller}"
  run_ros control set_controller_state "${controller}" active -c "${controller_manager}" \
    || fail "Failed to activate ${controller}."
fi

# CLI success alone is insufficient; observe all final states and ownership.
refresh_controllers
for name in mios_effort_controller mios_joint_position_controller; do
  if [[ "${states[${name}]:-}" != inactive ]]; then
    fail "${name} is ${states[${name}]:-missing}, expected inactive."
  fi
done
if [[ "${states[${controller}]:-}" != active ]]; then
  fail "${controller} is ${states[${controller}]:-missing}, expected active."
fi

echo "${controller} is active; effort and joint-position controllers are prepared inactive."
