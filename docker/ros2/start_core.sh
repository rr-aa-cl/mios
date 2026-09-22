#!/usr/bin/env bash
set -euo pipefail

# Container defaults live with the image so Docker and Kubernetes run the
# same Core service. ROS setup is sourced by /entrypoint.sh.
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
  -p allow_robot_parameter_application:=false \
  "$@"
