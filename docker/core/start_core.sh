#!/usr/bin/env bash
# Starts the MIOS Core and Portal. The image entrypoint supplies the ROS
# environment. Docker Compose and Kubernetes both run this script; the
# defaults below are the only place Core's start-up defaults are defined.
#
# Optional start-up steps (environment):
#   MIOS_NONRT_CPUS             pin Core to these CPUs (Compose uses `cpuset`)
#   MIOS_STARTUP_WAIT_SECONDS   wait this long for MongoDB before starting
set -euo pipefail
source "${MIOS_RUNTIME_LIB:-/usr/local/lib/mios/runtime_lib.sh}"

if [[ -n "${MIOS_NONRT_CPUS:-}" ]]; then
  pin_to_cpus "${MIOS_NONRT_CPUS}"
fi
wait_for_ports "${MIOS_STARTUP_WAIT_SECONDS:-0}" "${MONGO_PORT:-27017}"

exec /opt/mios/install/bin/mios_ros2_core_runtime --ros-args \
  -p "robot_ip:=${ROBOT_IP:-192.168.4.100}" \
  -p "database_name:=${MONGO_DB_NAME:-mios}" \
  -p "database_port:=${MONGO_PORT:-27017}" \
  -p "robot_configuration:=${ROBOT_CONFIG:-0}" \
  -p "websocket_port:=${MIOS_WS_PORT:-12000}" \
  -p "rpc_port:=${MIOS_RPC_PORT:-12001}" \
  -p "udp_port:=${MIOS_UDP_PORT:-12002}" \
  -p "enable_core_scheduler:=${MIOS_ENABLE_CORE_SCHEDULER:-true}" \
  -p "enable_core_task_execution:=${MIOS_ENABLE_CORE_TASK_EXECUTION:-true}" \
  -p "allow_controller_owned_move_mode:=${MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE:-true}" \
  -p "enable_joint_velocity_control:=${MIOS_ENABLE_JOINT_VELOCITY_CONTROL:-true}" \
  -p allow_robot_parameter_application:=true \
  "$@"
