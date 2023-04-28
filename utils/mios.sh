#!/bin/sh

ROOT=$(dirname "$(realpath $0)")
PYTHONPATH=$PYTHONPATH:${ROOT}/../python/desk:${ROOT}/../ml_service:/usr/local/lib/python3.8/dist-packages
export PYTHONPATH
#export ROS_MASTER_URI=http://localhost:11311
unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib:${ROOT}/../lib/boost:${ROOT}/../lib/plugins:${ROOT}/../../dependencies  # ${ROOT}/../lib/boost:/opt/ros/noetic/lib:
exec ${ROOT}/mios $@
exit 0
