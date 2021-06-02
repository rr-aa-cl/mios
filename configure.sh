#!/bin/sh -e

sudo apt-get install -y libboost1.65-all-dev libpoco-dev libeigen3-dev
sudo apt-get install libssl-dev libsasl2-dev libpoco-dev
sudo apt-get install -y libpython3.8
sudo apt-get install -y python3-pip

sudo pip3 install -U pytest numpy
sudo pip3 install conan

ROOT=$(dirname "$(realpath $0)")/third_party

mkdir -p ${ROOT}

# install json
cd ${ROOT}
if [ ! -d "json" ]
then
git clone https://github.com/nlohmann/json.git
fi
cd json
git checkout v3.9.1
mkdir -p build
cd build
cmake -DJSON_BuildTests=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

#install http-lib
cd ${ROOT}
if [ ! -d "cpp-httplib" ]
then
git clone https://github.com/yhirose/cpp-httplib.git
fi
cd cpp-httplib
git checkout v0.7.17
mkdir -p build
cd build
cmake -DHTTPLIB_COMPILE=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

#install json-rpccxx
cd ${ROOT}
if [ ! -d "json-rpc-cxx" ]
then
git clone https://github.com/jsonrpcx/json-rpc-cxx.git
fi
cd json-rpc-cxx
git checkout v0.2.1
mkdir -p build
cd build
cmake -DCOMPILE_TESTS=OFF -DCOMPILE_EXAMPLES=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

#install websocket
cd ${ROOT}
if [ ! -d "Simple-WebSocket-Server" ]
then
git clone https://gitlab.com/eidheim/Simple-WebSocket-Server.git
fi
cd Simple-WebSocket-Server
git checkout v2.0.2
mkdir -p build
cd build
cmake -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

#install spdlog
cd ${ROOT}
if [ ! -d "spdlog" ]
then
git clone https://github.com/gabime/spdlog.git
fi
cd spdlog
git checkout v1.8.1
mkdir -p build
cd build
cmake -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

#install pybind11
cd ${ROOT}
if [ ! -d "pybind11" ]
then
git clone https://github.com/pybind/pybind11.git
fi
cd pybind11
git checkout v2.6.1
mkdir -p build
cd build
cmake -DPYBIND11_PYTHON_VERSION=3.6 -DPYBIND11_TEST=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} -DPYTHON_EXECUTABLE:FILEPATH=/usr/bin/python3.6 ..
make -j$(nproc --all)
make install

# install cxxopts
cd ${ROOT}
if [ ! -d "cxxopts" ]
then
git clone https://github.com/jarro2783/cxxopts.git
fi
cd cxxopts
git checkout v2.2.1
mkdir -p build
cd build
cmake -DCMAKE_INSTALL_PREFIX=${ROOT} -DCXXOPTS_BUILD_EXAMPLES=OFF -DCXXOPTS_BUILD_TESTS=OFF ..
make -j$(nproc --all)
make install

#install msrm_utils
cd ${ROOT}
if [ ! -d "msrm_utils" ]
then
git clone https://gitlab.lrz.de/ge29miq/msrm_utils.git
fi
cd msrm_utils
git checkout v1.3.1
mkdir -p build/release
cd build/release
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} ../..
make -j$(nproc --all)
make install

# install libmongoc
cd ${ROOT}
if [ ! -d "mongo-c-driver" ]
then
git clone https://github.com/mongodb/mongo-c-driver.git --branch r1.17
fi
cd mongo-c-driver
mkdir -p cmake-build
cd cmake-build
cmake -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF -DENABLE_STATIC=ON -DENABLE_TESTS=OFF -DENABLE_EXAMPLES=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc --all)
make install

# install mongocxx
cd ${ROOT}
if [ ! -d "mongo-cxx-driver" ]
then
git clone https://github.com/mongodb/mongo-cxx-driver.git
fi
cd mongo-cxx-driver
git checkout r3.6.2
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DCMAKE_PREFIX_PATH=${ROOT} -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make EP_mnmlstc_core
make -j$(nproc --all)
make install

#install libfranka
cd ${ROOT}
if [ ! -d "libfranka" ]
then
git clone --recurse-submodules https://github.com/frankaemika/libfranka.git
fi
cd libfranka
git checkout 0.8.0
git submodule update
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DBUILD_EXAMPLES=OFF -DCMAKE_INSTALL_PREFIX=${ROOT} ..
make -j$(nproc --all)
make install

