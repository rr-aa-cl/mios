#!/bin/sh

ROOT=$(dirname "$(realpath $0)")
PYTHONPATH=$PYTHONPATH:${ROOT}/../python/desk:${ROOT}/../ml_service:/usr/local/lib/python3.10/dist-packages
export PYTHONPATH
#export ROS_MASTER_URI=http://localhost:11311
unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib:${ROOT}/../lib/boost:${ROOT}/../lib/plugins:${ROOT}/../../dependencies:/opt/openrobots/lib      #ROS ${ROOT}/../lib/boost:/opt/ros/noetic/lib:
exec ${ROOT}/mios \
    ${verbosity:+--verbosity=$verbosity} \
    ${database_port:+--database_port=$database_port} \
    ${database_name:+--database_name=$database_name} \
    ${robot_ip:+--robot_ip=$robot_ip} \
    ${websocket_port:+--websocket_port=$websocket_port} \
    ${rpc_port:+--rpc_port=$rpc_port} \
    ${udp_port:+--udp_port=$udp_port} \
    ${robot_config:+--robot_config=$robot_config} \
    ${robot_arm:+--robot_arm=$robot_arm} \
    ${desk:+--desk=$desk} \
    "$@"
exit 0
