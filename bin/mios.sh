#!/bin/sh

ARG1="$1"
ROOT=$(dirname "$(realpath $0)")
PYTHONPATH=$PYTHONPATH:${ROOT}/../python/desk:${ROOT}/../ml_service:/usr/local/lib/python3.6/dist-packages
export PYTHONPATH
export ROS_MASTER_URI=http://localhost:11311
unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib:${ROOT}/../lib/plugins:/opt/ros/melodic/lib:${ROOT}/../../dependencies
exec ${ROOT}/mios $ARG1
exit 0
