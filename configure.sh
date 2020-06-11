#!/bin/sh -e

sudo apt-get install -y libboost1.65-all-dev libpoco-dev libeigen3-dev

ROOT=$(dirname "$(realpath $0)")

# install json
cd ${ROOT}/third_party
git clone https://github.com/nlohmann/json.git
cd json
git checkout v3.7.3
cp -r include/nlohmann ${ROOT}/third_party/include/

#install http-lib
cd ${ROOT}/third_party
git clone https://github.com/yhirose/cpp-httplib.git
cd cpp-httplib
git checkout v0.6.6

#install json-rpccxx
cd ${ROOT}/third_party
git clone https://github.com/jsonrpcx/json-rpc-cxx.git
cd json-rpc-cxx
git checkout v0.1.0
cp include/jsonrpccxx/* ${ROOT}/third_party/include/jsonrpccxx

#install websocket
cd ${ROOT}/third_party
git clone https://gitlab.com/eidheim/Simple-WebSocket-Server.git
cd Simple-WebSocket-Server
git checkout v2.0.0
cp *.hpp ${ROOT}/third_party/include/simple-websocket-server/
