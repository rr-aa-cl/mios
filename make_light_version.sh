#!/bin/sh -e

ROOT=$(dirname "$(realpath $0)")

./install.sh

if [ -d ../mios_light/lib ]; then
  rm -r ../mios_light/lib
fi
if [ -d ../mios_light/plugins ]; then
  rm -r ../mios_light/plugins
fi

rsync -ra --relative plugins/* ../mios_light/
rsync -r config ../mios_light/
rsync -r lib ../mios_light/

rsync -a --relative python/led/aurora.py ../mios_light/
rsync -a --relative python/led/config.py ../mios_light/
rsync -a --relative python/desk/desk_server.py ../mios_light/
rsync -a --relative python/led/led_server.py ../mios_light/
rsync -a --relative python/utils/meta_coding.py ../mios_light/
rsync -a --relative python/utils/rpc_client.py ../mios_light/
rsync -a --relative python/utils/ws_client.py ../mios_light/
rsync -a --relative python/led/setup.py ../mios_light/

rm ../mios_light/lib/tasks/*
rm ../mios_light/lib/skills/*
rm ../mios_light/lib/primitives/*
rm ../mios_light/lib/led_patterns/*

rsync -a --relative doc/mios_doxy ../mios_light/

rsync -a --relative task/src/tasks/* ../mios_light/
rsync -a --relative task/include/tasks/* ../mios_light/
rsync -a --relative skill/src/skills/* ../mios_light/
rsync -a --relative skill/include/skills/* ../mios_light/
rsync -a --relative manipulation_primitive/src/primitives/* ../mios_light/
rsync -a --relative manipulation_primitive/include/primitives/* ../mios_light/
rsync -a --relative led_pattern/src/patterns/* ../mios_light/
rsync -a --relative led_pattern/include/patterns/* ../mios_light/

rsync -a --relative cpp/include/cpp_utils/* ../mios_light/
rsync -a --relative bin/* ../mios_light/
rsync -a --relative task/include/task/task.hpp ../mios_light/
rsync -a --relative task/include/task/task_list.hpp ../mios_light/
rsync -a --relative skill/include/skill/skill.hpp ../mios_light/
rsync -a --relative skill/include/skill/header_skills.hpp ../mios_light/
rsync -a --relative led_pattern/include/led_pattern/led_pattern.hpp ../mios_light/
rsync -a --relative led_pattern/include/led_pattern/header_led_patterns.hpp ../mios_light/
rsync -a --relative manipulation_primitive/include/manipulation_primitive/manipulation_primitive.hpp ../mios_light/
rsync -a --relative knowledge_base/include/knowledge_base/concepts.hpp ../mios_light/
rsync -a --relative knowledge_base/include/knowledge_base/local_memory.hpp ../mios_light/
rsync -a --relative knowledge_base/include/knowledge_base/knowledge_base.hpp ../mios_light/
rsync -a --relative utils/include/utils/* ../mios_light/

rsync -a --relative task/src/task_list.cpp ../mios_light/

cd ${ROOT}/..
cp -r mios_light mios_package
if [ -f mios_package/CMakeLists.txt.user ]; then
    rm mios_package/CMakeLists.txt.user
fi
if [ -d mios_package/build ]; then
  rm -r mios_package/build/*
fi
if [ -d mios_package/mios_package ]; then
  rm -r mios_package/mios_package
fi
if [ -d mios_package/python/__pycache__ ]; then
  rm -r mios_package/python/__pycache__
fi
tar -zcvf mios_release.tar.gz -C mios_package .
rm -r mios_package
