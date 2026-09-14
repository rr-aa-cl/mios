#!/usr/bin/env bash
# The image entrypoint supplies the ROS environment. Keep all Control startup
# and child-process ownership inside this container, including after restart.
set -euo pipefail

if (( $# != 0 )); then
  echo "start_control.sh takes configuration through ROBOT_IP and MIOS_* environment variables." >&2
  exit 2
fi

state_dir="${MIOS_CONTROL_STATE_DIR:-/run/mios-control}"
worker_cpus="${MIOS_CONTROL_WORKER_CPUS:-0-5,8-19}"
load_gripper="${MIOS_LOAD_GRIPPER:-true}"
if [[ "${load_gripper}" != true && "${load_gripper}" != false ]]; then
  echo "MIOS_LOAD_GRIPPER must be true or false." >&2
  exit 2
fi
mkdir -p "${state_dir}"
rm -f "${state_dir}/ready"
launch_pid=""
prepare_pid=""

children_alive() {
  local pid
  for pid in "${prepare_pid}" "${launch_pid}"; do
    if [[ -n "${pid}" ]] && kill -0 -- "-${pid}" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

cleanup() {
  trap - EXIT INT TERM
  rm -f "${state_dir}/ready"
  [[ -z "${prepare_pid}" ]] || kill -TERM -- "-${prepare_pid}" 2>/dev/null || true
  [[ -z "${launch_pid}" ]] || kill -INT -- "-${launch_pid}" 2>/dev/null || true
  local deadline=$((SECONDS + 10)) pid
  while children_alive && (( SECONDS < deadline )); do sleep 0.1; done
  for pid in "${prepare_pid}" "${launch_pid}"; do
    [[ -z "${pid}" ]] || kill -TERM -- "-${pid}" 2>/dev/null || true
  done
  deadline=$((SECONDS + 2))
  while children_alive && (( SECONDS < deadline )); do sleep 0.1; done
  for pid in "${prepare_pid}" "${launch_pid}"; do
    if [[ -n "${pid}" ]]; then
      kill -KILL -- "-${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Each process group includes its children so cancellation cannot leave a
# pending controller-preparation command behind the launch process.
setsid taskset --cpu-list "${worker_cpus}" \
  ros2 launch franka_bringup franka.launch.py \
    robot_type:=fr3 "robot_ip:=${ROBOT_IP:-192.168.4.100}" \
    "load_gripper:=${load_gripper}" \
    controllers_yaml:=/ws/install/mios_ros2_control/share/mios_ros2_control/config/mios_controllers.yaml &
launch_pid=$!
setsid taskset --cpu-list "${worker_cpus}" start_model_broadcaster.sh &
prepare_pid=$!

completed=""
status=0
wait -n -p completed "${launch_pid}" "${prepare_pid}" || status=$?
if [[ "${completed:-}" != "${prepare_pid}" || "${status}" != 0 ]]; then
  echo "Control startup failed: ROS launch exited or controller preparation failed (status ${status})." >&2
  exit 1
fi
prepare_pid=""

# Include the process start time so a stale marker cannot match a reused PID.
if [[ ! -r "/proc/${launch_pid}/stat" ]]; then
  echo "Control launch exited before preparation completed." >&2
  exit 1
fi
process_stat="$(< "/proc/${launch_pid}/stat")"
read -r -a process_fields <<< "${process_stat##*) }"
if [[ "${process_fields[0]}" == Z ]]; then
  echo "Control launch exited before preparation completed." >&2
  exit 1
fi
printf '%s %s\n' "${launch_pid}" "${process_fields[19]}" > "${state_dir}/ready"
echo "Control is ready: model broadcaster active; arm controllers prepared inactive."

status=0
wait "${launch_pid}" || status=$?
echo "Control launch exited (status ${status})." >&2
exit 1
