#!/bin/sh -e

IP="$1"
user="collective_dualarm"  #"panda"
ROOT=$(dirname "$(realpath $0)")
cd ${ROOT}

### make ros components ###
#cd ${ROOT}/src/ros_workspace
#catkin_make

### make ###
cd ${ROOT}
mkdir -p ${ROOT}/build/Release

cd ${ROOT}/build/Release
cmake -DCMAKE_INSTALL_PREFIX=${ROOT}/mios ../..

make -j$(nproc --all) install
#make  install
cd ${ROOT}

if [ ! -z "$1" ];
then
rsync -rl mios $user@$IP:~/
fi
