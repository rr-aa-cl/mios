# syntax=docker/dockerfile:1

# Core imports only the Control image's published ROS transport artifacts. It
# does not inherit the hardware image filesystem or its FCI/libfranka runtime.
ARG MIOS_CONTROL_IMAGE=mios-ros2-control:local
FROM ${MIOS_CONTROL_IMAGE} AS control_artifacts

# Match Control's pinned ROS base for the imported transport artifacts.
FROM osrf/ros:jazzy-desktop@sha256:e1c05248ece3bc328386d0509a041a97a5de872a5606418118748875c539c66f

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG MIOS_CORE_CONTRACT_VERSION=0.1.0
LABEL org.opencontainers.image.title="mios-ros2-core" \
      io.mios.core-contract.version="${MIOS_CORE_CONTRACT_VERSION}"
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /ws

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpoco-dev nlohmann-json3-dev fping python3-pip python3-websockets \
    && rm -rf /var/lib/apt/lists/*

# The Control workspace uses colcon's symlink-install layout. Retain the
# installed transport and its build artifacts, without the control image's
# Franka hardware sources or libfranka runtime.
COPY --from=control_artifacts /ws/install /ws/install
COPY --from=control_artifacts /ws/build /ws/build
# colcon's --symlink-install package exports public runtime headers through
# this source path. Copy only that transport header tree, never the Franka
# hardware sources or libfranka runtime.
COPY --from=control_artifacts /ws/src/mios_ros2_runtime/include /ws/src/mios_ros2_runtime/include

# Core owns this build and all of its Portal/task artifacts. It links only
# against the ROS transport packages copied above.
COPY mios/CMakeLists.txt mios/conanfile.txt /opt/mios/
COPY mios/cmake /opt/mios/cmake
COPY mios/include /opt/mios/include
COPY mios/src /opt/mios/src
RUN python3 -m pip install --target /opt/mios-conan conan==1.66.0
RUN --mount=type=cache,target=/root/.conan \
    source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && export PATH=/opt/mios-conan/bin:${PATH} PYTHONPATH=/opt/mios-conan:${PYTHONPATH} \
    && cmake -S /opt/mios -B /opt/mios/build \
         -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_INSTALL_PREFIX=/opt/mios/install \
         '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib' \
         -DMIOS_BUILD_ROS2_CORE_RUNTIME=ON \
         -DENABLE_TESTING=ON \
         -DENABLE_PCH=OFF \
    && cmake --build /opt/mios/build \
         --target mios_ros2_core_runtime test_joint_position_pipeline test_ff_strategy --parallel 2 \
    && ctest --test-dir /opt/mios/build --output-on-failure \
         --tests-regex '^(test_joint_position_pipeline|test_ff_strategy)$' \
    && cmake --install /opt/mios/build \
    && install -d /opt/mios/install/lib \
    && cp -a /opt/mios/build/lib/boost/libboost_*.so* /opt/mios/install/lib/

# Core loads its retained MIOS controller and safety plugins dynamically.
RUN find /opt/mios/src/plugins -type f -name 'lib*.so' \
    -exec cp -a {} /opt/mios/install/lib/ \;

COPY mios/python/utils/ws_client.py /opt/mios/python/utils/ws_client.py
COPY mios/docker/ros2/entrypoint.sh /entrypoint.sh
COPY mios/docker/ros2/start_core.sh /usr/local/bin/start_core.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/start_core.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/start_core.sh"]
