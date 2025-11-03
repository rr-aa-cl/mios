FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.10 \
    libpython3.10 \
    python3-pip \
    fping \
    curl \
    gnupg \
    lsb-release
RUN mkdir -p /etc/apt/keyrings && \
    curl http://robotpkg.openrobots.org/packages/debian/robotpkg.asc | tee /etc/apt/keyrings/robotpkg.asc && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/robotpkg.asc] http://robotpkg.openrobots.org/packages/debian/pub $(lsb_release -cs) robotpkg" | tee /etc/apt/sources.list.d/robotpkg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    robotpkg-pinocchio && \
    # Clean up apt caches to keep the image small
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install -U setuptools
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install -U pymongo
RUN pip3 install -U scikit-learn
RUN pip3 install -U requests
RUN pip3 install -U pyDOE scikit-optimize
RUN pip3 install -U websockets
RUN pip3 install -U requests
RUN pip3 install -U urwid



COPY mios/ /mios/
COPY dependencies/ /dependencies/
RUN chmod +x /mios/bin/mios.sh
RUN chmod +x /mios/bin/mios

EXPOSE 12000 12001 12002 8888 8889

ARG default_verbosity_value=info
ARG default_database_port_value=27017
ARG default_robot_config_value=3
ARG default_robot_arm_value=left
ENV verbosity=$default_verbosity_value
ENV database_port=$default_database_port_value
ENV robot_config=$default_robot_config_value
ENV robot_arm=$default_robot_arm_value
ENV LD_LIBRARY_PATH=/opt/openrobots/lib:/dependencies:/mios/lib:$LD_LIBRARY_PATH

WORKDIR mios/bin
CMD ["sh", "-c", "bash ./mios.sh --verbosity=${verbosity} --database_port=${database_port} --robot_config=${robot_config} --robot_arm=${robot_arm}"]
