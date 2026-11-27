# syntax=docker/dockerfile:1

# Two stages:
#   build    compilers, Conan, the MIOS sources and the CMake build tree
#   runtime  the default target: ROS runtime, the ROS transport overlay and
#            /opt/mios/install only
#
# Build context is the parent directory of the `mios` checkout. Core needs the
# Control image. The simplest way is to let bake build both, which links Core
# to the Control build of the same run:
#   docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=..
# To build Core alone against an existing Control image, name it explicitly:
#   docker build -f docker/core/Dockerfile -t <repo>/ros2-core:latest \
#     --build-arg MIOS_CONTROL_IMAGE=<repo>/ros2-control:latest ..

# Core imports only the Control image's published ROS transport artifacts. It
# does not inherit the hardware image filesystem or its FCI/libfranka runtime.
ARG MIOS_CONTROL_IMAGE=janine86/ros2-control:abcdefghijlatest
FROM ${MIOS_CONTROL_IMAGE} AS control_artifacts

###############################################################################
FROM ros:jazzy-ros-base AS build

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /ws

# Tooling first: none of these layers depend on the MIOS sources, so a source
# edit goes straight to the compile step below.
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      ccache fping libpoco-dev ninja-build nlohmann-json3-dev python3-pip
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install \
        --target /opt/mios-conan \
        --no-compile \
        conan==1.66.0

# The Control image installs its workspace with plain (copying) installs, so
# /ws/install carries the transport libraries, headers and CMake packages by
# itself. No Franka hardware sources or libfranka runtime are copied.
COPY --from=control_artifacts /ws/install /ws/install

# Core owns this build and all of its Portal/task artifacts. It links only
# against the ROS transport packages copied above.
COPY mios/CMakeLists.txt mios/conanfile.txt /opt/mios/
COPY mios/cmake /opt/mios/cmake
COPY mios/include /opt/mios/include
COPY mios/src /opt/mios/src

RUN --mount=type=cache,target=/root/.conan \
    --mount=type=cache,target=/root/.cache/ccache \
    source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && export PATH=/opt/mios-conan/bin:${PATH} \
    && export PYTHONPATH=/opt/mios-conan:${PYTHONPATH} \
    && export CCACHE_DIR=/root/.cache/ccache \
    && export CCACHE_MAXSIZE=5G \
    && export CCACHE_BASEDIR=/opt/mios \
    && echo "Available CPUs: $(nproc)" \
    && echo "Starting MIOS CMake configuration..." \
    && time cmake -S /opt/mios -B /opt/mios/build-ninja \
         -G Ninja \
         -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_INSTALL_PREFIX=/opt/mios/install \
         '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib' \
         -DCMAKE_C_COMPILER_LAUNCHER=ccache \
         -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
         -DMIOS_BUILD_ROS2_CORE_RUNTIME=ON \
         -DENABLE_TESTING=ON \
         -DENABLE_PCH=OFF \
    && echo "Starting MIOS compilation..." \
    && time cmake --build /opt/mios/build-ninja \
         --target mios_ros2_core_runtime test_joint_position_pipeline test_ff_strategy \
         --parallel $(nproc) \
    && echo "Starting MIOS tests..." \
    && time ctest --test-dir /opt/mios/build-ninja \
         --output-on-failure \
         --tests-regex '^(test_joint_position_pipeline|test_ff_strategy)$' \
    && echo "Installing MIOS..." \
    && time cmake --install /opt/mios/build-ninja \
    && install -d /opt/mios/install/lib \
    && cp -a /opt/mios/build-ninja/lib/boost/libboost_*.so* /opt/mios/install/lib/ \
    # Core loads its retained MIOS controller and safety plugins dynamically.
    && find /opt/mios/src/plugins -type f -name 'lib*.so' \
         -exec cp -a {} /opt/mios/install/lib/ \; \
    && ccache -s

###############################################################################
FROM ros:jazzy-ros-core AS runtime

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG MIOS_CORE_CONTRACT_VERSION=0.1.0
LABEL org.opencontainers.image.title="mios-ros2-core" \
      io.mios.core-contract.version="${MIOS_CORE_CONTRACT_VERSION}"
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /ws

RUN apt-get update && apt-get install -y --no-install-recommends \
      fping python3-websockets \
    && rm -rf /var/lib/apt/lists/*

COPY --from=control_artifacts /ws/install /ws/install
COPY --from=build /opt/mios/install /opt/mios/install

COPY mios/python/utils/ws_client.py /opt/mios/python/utils/ws_client.py
COPY --chmod=755 mios/docker/common/entrypoint.sh /entrypoint.sh
COPY mios/docker/common/runtime_lib.sh /usr/local/lib/mios/runtime_lib.sh
COPY --chmod=755 mios/docker/core/start_core.sh \
                 mios/docker/core/check_core_ready.sh /usr/local/bin/

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/start_core.sh"]
