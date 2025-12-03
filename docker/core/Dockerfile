FROM ubuntu:24.04
RUN apt-get update && apt-get install -y \
	python3.12 python3-pip python3.12-venv \
	&& rm -rf /var/lib/apt/lists/*
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install numpy
RUN pip install scipy
RUN pip install pymongo
RUN pip install scikit-learn
RUN pip install requests
RUN pip install pyDOE scikit-optimize
RUN pip install websockets
RUN apt-get update && apt-get install -y fping && rm -rf /var/lib/apt/lists/*
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

WORKDIR /mios/bin
CMD ["/bin/sh", "-c", "./mios.sh --verbosity=${verbosity} --database_port=${database_port} --robot_config=${robot_config} --robot_arm=${robot_arm}"]
