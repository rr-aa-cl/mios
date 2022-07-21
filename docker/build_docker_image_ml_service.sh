#!/bin/sh -e

read -p "Enter registry: " registry

ROOT=$(dirname "$(realpath $0)")/..
cd ${ROOT}

docker build --network=host -t mios_mls -f docker/ml_service/Dockerfile .
docker tag mios_mls ${registry}/mios_mls

# read -p "Upload the image to regestry?" confirm  

# docker push ${registry}/mios_mls
