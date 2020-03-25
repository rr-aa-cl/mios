#!/bin/sh -e

ROOT=$(dirname "$(realpath $0)")/..
cd ${ROOT}

docker build -t mios_ml -f docker/ml/Dockerfile .
docker tag mios_ml:latest tueirsi-pc-020.local:5000/mios_ml
