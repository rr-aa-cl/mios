#!/bin/sh -e

# collect dependencies

ROOT=$(dirname "$(realpath $0)")/..
cd ${ROOT}

# build mios
${ROOT}/install.sh

if [ ! -d "${ROOT}/mios/lib" ]; then
echo "Library folder does not exist."
exit
fi

if [ ! -d "${ROOT}/dependencies" ]; then
mkdir ${ROOT}/dependencies
fi

cd ${ROOT}/mios/lib
for f in ${ROOT}/mios/lib/* ; do
if [ -f $f ]; then
ldd $f | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' ${ROOT}/dependencies
fi
done

if [ ! -d "${ROOT}/mios/bin" ]; then
echo "Binary folder does not exist."
exit
fi

cd ${ROOT}/mios/bin
ldd mios | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' ${ROOT}/dependencies

cd ${ROOT}

docker build -t mios -f docker/core/Dockerfile .
docker tag mios:latest msrm/mios:release
docker tag mios:latest collective-control-001.local:5000/mios

rm -r ${ROOT}/dependencies
