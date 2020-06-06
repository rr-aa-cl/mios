#!/bin/sh -e

cd

sudo apt-get install -y libboost1.65-all-dev
sudo apt-get install -y build-essential cmake git libpoco-dev libeigen3-dev ssh
sudo apt-get install -y libzstd-dev libsasl2-dev libsnappy-dev zlib1g-dev
sudo apt-get install -y libsdl2-2.0-0 libsdl2-dev libsdl2-mixer-2.0-0 libsdl2-mixer-dev

sudo apt-get install -y ipython3
sudo apt-get install -y python3-pip

sudo -H pip install -U pymongo
sudo -H pip install -U werkzeug
sudo -H pip install -U json-rpc
sudo -H pip install -U websockets


n_cpu_total=$(nproc --all)
ceil() {
  echo $((($n_cpu_total+2-1)/2))
}
n_cpu=$(ceil)


# install libmongoc (v1.15)
git clone https://github.com/mongodb/mongo-c-driver.git --branch r1.17
cd mongo-c-driver
mkdir cmake-build
cd cmake-build
cmake -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF -DCMAKE_BUILD_TYPE=Release ..
make -j$n_cpu
sudo make install

cd ../..
sudo rm -r mongo-c-driver

# install mongocxx (latest version)
git clone https://github.com/mongodb/mongo-cxx-driver.git --branch releases/v3.5
cd mongo-cxx-driver/build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local ..
sudo make EP_mnmlstc_core
make -j$n_cpu
sudo make install
cd ../..
sudo rm -r mongo-cxx-driver
sudo ldconfig

# nlohman json

git clone https://github.com/nlohmann/json.git
cd json
git checkout v3.7.3
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc --all)
sudo make install

cd ../..
sudo rm -r json
