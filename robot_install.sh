#!/bin/sh -e

cd

sudo apt-get install -y libboost1.65-all-dev
sudo apt-get install -y libpython3.8
sudo apt-get install -y build-essential cmake git libpoco-dev libeigen3-dev ssh
sudo apt-get install -y fping

wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt-get update
sudo apt-get install mongodb-org=4.4.2 mongodb-org-mongos=4.4.2 mongodb-org-server=4.4.2 mongodb-org-tools=4.4.2 mongodb-org-shell=4.4.2
sudo apt-mark hold mongodb-org*
sudo sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mongod.conf
sudo systemctl enable mongod.service
sudo systemctl start mongod.service


sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt install gcc-9 g++-9

