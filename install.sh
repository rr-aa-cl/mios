#!/bin/sh -e

IP="$1"
user="panda"
ROOT=$(dirname "$(realpath $0)")
cd ${ROOT}

### make ros components ###
cd ${ROOT}/ros_workspace
catkin_make

### make ###
cd ${ROOT}
mkdir -p ${ROOT}/build/release

cd ${ROOT}/build/release
cmake ../..
make -j$(nproc --all) install

### collect shared libraries ###
cp ${ROOT}/third_party/lib/libfranka* ${ROOT}/lib/

cd ${ROOT}

if [ ! -z "$1" ];
then
rsync -r bin $user@$IP:~/mios/
rsync -r lib $user@$IP:~/mios/
rsync -r python $user@$IP:~/mios/
else
{
if [ ! -d "${ROOT}/mios_package" ]; then
rm -r mios_package/
fi
} || {
:
}
rsync -ar --relative bin mios_package/
rsync -ar --relative lib mios_package/
rsync -ar --relative python mios_package/
fi
