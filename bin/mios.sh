#!/bin/sh


ROOT=$(dirname "$(realpath $0)")

unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib/plugins:/opt/ros/melodic/lib
exec ${ROOT}/mios
