FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y python3.8 libpython3.8
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip3 install -U setuptools
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install -U pymongo
RUN pip3 install -U scikit-learn
RUN pip3 install -U requests
RUN pip3 install -U pyDOE scikit-optimize
RUN pip3 install -U websockets
RUN apt-get install -y fping
COPY mios/ /mios/
COPY dependencies/ /dependencies/

EXPOSE 12000 12001 12002 8888 8889

ARG default_verbosity_value=info
ARG default_database_port_value=27017
ARG default_robot_config_value=3
ARG default_robot_arm_value=left
ENV verbosity=$default_verbosity_value
ENV database_port=$default_database_port_value
ENV robot_config=$default_robot_config_value
ENV robot_arm=$default_robot_arm_value

WORKDIR mios/bin
CMD ["sh", "-c", "./mios.sh --verbosity=${verbosity} --database_port=${database_port} --robot_config=${robot_config} --robot_arm=${robot_arm}"]
