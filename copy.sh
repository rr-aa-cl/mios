#!/bin/sh -e

### push all libraries ###

IP="$1"

ROOT=$(dirname "$(realpath $0)")
cd ${ROOT}

if [ ! -z "$1" ];
then
rsync -e "ssh -o StrictHostKeyChecking=no" -r bin panda@$IP:~/mios/
rsync -e "ssh -o StrictHostKeyChecking=no" -r lib panda@$IP:~/mios/
rsync -e "ssh -o StrictHostKeyChecking=no" -r config panda@$IP:~/mios/
rsync -e "ssh -o StrictHostKeyChecking=no" -r python panda@$IP:~/mios/
rsync -e "ssh -o StrictHostKeyChecking=no" -r ml_methods panda@$IP:~/mios/
rsync -e "ssh -o StrictHostKeyChecking=no" start.py panda@$IP:~/mios/
fi
