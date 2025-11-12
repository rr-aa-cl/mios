FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential cmake git libpoco-dev libeigen3-dev libfmt-dev \
    lsb-release curl

RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL http://robotpkg.openrobots.org/packages/debian/robotpkg.asc | tee /etc/apt/keyrings/robotpkg.asc && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/robotpkg.asc] http://robotpkg.openrobots.org/packages/debian/pub $(lsb_release -cs) robotpkg" | tee /etc/apt/sources.list.d/robotpkg.list


RUN apt-get update && apt-get install -y \
    robotpkg-pinocchio
    
# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    fping
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Set python and pip aliases
# RUN ln -s /usr/bin/python3 /usr/bin/python
   
RUN pip install "conan==1.66.0" numpy

# RUN apt update && apt install -y \
#     clang-format clang-tidy


ENV CC=/usr/bin/gcc

ENV PATH=/opt/openrobots/bin:$PATH
ENV PKG_CONFIG_PATH=/opt/openrobots/lib/pkgconfig:$PKG_CONFIG_PATH
ENV LD_LIBRARY_PATH=/opt/openrobots/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH=/opt/openrobots/lib/python3.10/site-packages:$PYTHONPATH
ENV CMAKE_PREFIX_PATH=/opt/openrobots:$CMAKE_PREFIX_PATH
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     cmake \
#     git \
#     libpoco-dev \
#     libeigen3-dev \
#     libfmt-dev \
#     ninja-build \
#     ccache \
#     gdb \
#     lcov \
#     clang \
#     libspdlog-dev \
#     libboost-all-dev \
#     libeigen3-dev \
#     libyaml-cpp-dev \
#     libprotobuf-dev protobuf-compiler \
#     lsb-release \
#     curl \
#     && rm -rf /var/lib/apt/lists/*sts/*

# RUN mkdir -p /etc/apt/keyrings
# #RUN curl -fsSL http://robotpkg.openrobots.org/packages/debian/robotpkg.asc | tee /etc/apt/keyrings/robotpkg.asc
# #RUN echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/robotpkg.asc] http://robotpkg.openrobots.org/packages/debian/pub $(lsb_release -cs) robotpkg" | tee /etc/apt/sources.list.d/robotpkg.list
# #RUN apt-get update && apt-get install -y robotpkg-py38-robotpkg
# # RUN conan profile detect --force

# # RUN git clone git@github.com:ciai-engineering/mios.git /mios
# # ENV LD_LIBRARY_PATH=${ROOT}/../lib:${ROOT}/../lib/boost:${ROOT}/../lib/plugins:${ROOT}/../../dependencies:/opt/openrobots/lib




# Mios build dependencies:
# cmake
# fping
# libpoco-dev
# libeigen3-dev
# python3.10
# libpython3.10
# robotpkg-pinocchio*
 
# *The script for installing robotpkg-pinocchio:
# mkdir -p /etc/apt/keyrings && \
#     curl http://robotpkg.openrobots.org/packages/debian/robotpkg.asc | tee /etc/apt/keyrings/robotpkg.asc && \
#     echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/robotpkg.asc] http://robotpkg.openrobots.org/packages/debian/pub $(lsb_release -cs) robotpkg" | tee /etc/apt/sources.list.d/robotpkg.list && \
#     apt-get update && \
#     apt-get install -y --no-install-recommends \
#     robotpkg-pinocchio
 