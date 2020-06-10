#!/bin/sh


ROOT=$(dirname "$(realpath $0)")
PYTHONPATH=$PYTHONPATH:${ROOT}/../python/desk
export PYTHONPATH
unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib/plugins:/opt/ros/melodic/lib
exec ${ROOT}/mios
