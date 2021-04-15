#!/usr/bin/env bash

read -p "Enter hostname: "  host
read -p "Enter username: "  user
read -s -p "Enter password: "  pw

sshpass -p ${pw} ssh -t ${user}@${host} "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add"
sshpass -p ${pw} ssh -t ${user}@${host} 'sudo apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"'
sshpass -p ${pw} ssh -t ${user}@${host} "sudo apt-get install -y kubeadm=1.19.2-00 kubelet=1.19.2-00 kubectl=1.19.2-00"

sshpass -p ${pw} ssh -t ${user}@${host} "sudo sed -i '/ swap / s/^/#/' /etc/fstab"
sshpass -p ${pw} ssh -t ${user}@${host} "sudo swapoff -a"

token=$(kubeadm token generate)
master=$(hostname -s)

sudo kubeadm token create ${token}

sshpass -p ${pw} ssh -t ${user}@${host} "sudo kubeadm join --discovery-token-unsafe-skip-ca-verification --token=${token} ${master}:6443"
