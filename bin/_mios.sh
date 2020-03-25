#!/bin/sh


ROOT=$(dirname "$(realpath $0)")

unset LD_LIBRARY_PATH
export LD_LIBRARY_PATH=${ROOT}/../lib:${ROOT}/../lib/primitives:${ROOT}/../lib/skills:${ROOT}/../lib/tasks:${ROOT}/../lib/plugins:${ROOT}/../lib/led_patterns:${ROOT}/../../dependencies
exec ${ROOT}/mios
