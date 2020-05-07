#!/bin/sh -e

IP="$1"
user="panda"
ROOT=$(dirname "$(realpath $0)")
cd ${ROOT}

n_cpu_total=$(nproc --all)

ceil() {
  echo $((($n_cpu_total+2-1)/2))
}

n_cpu=$(ceil)

### refresh code ###

### copy all plugins ###
if [ ! -d "${ROOT}/lib" ]; then
mkdir ${ROOT}/lib
fi

if [ ! -d "${ROOT}/lib/plugins" ]; then
mkdir ${ROOT}/lib/plugins
fi

cd ${ROOT}
cp -r plugins/lib/* lib/plugins/

### make ###
if [ ! -d "${ROOT}/build" ]; then
mkdir ${ROOT}/build
fi

if [ ! -d "${ROOT}/build/release" ]; then
mkdir ${ROOT}/build/release
fi

cd ${ROOT}/build/release
cmake ../..
make -j$n_cpu install

### push all libraries ###

cd ${ROOT}

if [ ! -z "$1" ];
then
rsync -r bin $user@$IP:~/mios/
rsync -r lib $user@$IP:~/mios/
rsync -r python $user@$IP:~/mios/
rsync -r ml_methods $user@$IP:~/mios/
rsync start.py $user@$IP:~/mios/
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
rsync -ar --relative ml_methods mios_package/
rsync -a --relative start.py mios_package/
fi
