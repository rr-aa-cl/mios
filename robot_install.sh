#!/bin/sh -e

cd

sudo apt-get install -y libboost1.65-all-dev
sudo apt-get install -y python3.8-dev
sudo apt-get install -y build-essential cmake git libpoco-dev libeigen3-dev ssh

wget -qO - https://www.mongodb.org/static/pgp/server-4.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
sudo apt-get update
sudo apt-get install mongodb-org=4.0.18 mongodb-org-mongos=4.0.18 mongodb-org-server=4.0.18 mongodb-org-tools=4.0.18 mongodb-org-shell=4.0.18
sudo systemctl enable mongodb.service
sudo systemctl start mongodb.service

n_cpu_total=$(nproc --all)
ceil() {
  echo $((($n_cpu_total+2-1)/2))
}
n_cpu=$(ceil)


# install libmongoc (v1.15)
git clone https://github.com/mongodb/mongo-c-driver.git --branch r1.15
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
