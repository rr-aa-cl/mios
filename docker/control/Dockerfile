ARG MIOS_CORE_CONTRACT_VERSION=0.1.0

# Retain the ROS base used by the commissioned Control build. Rebuilding a
# startup script must not silently replace the underlying ROS/system packages.
FROM osrf/ros:jazzy-desktop@sha256:e1c05248ece3bc328386d0509a041a97a5de872a5606418118748875c539c66f

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG MIOS_CORE_CONTRACT_VERSION
LABEL org.opencontainers.image.title="mios-ros2-control" \
      io.mios.core-contract.version="${MIOS_CORE_CONTRACT_VERSION}"
ENV DEBIAN_FRONTEND=noninteractive
# Building libfranka and the hardware plugin concurrently can exceed the
# memory available to a desktop Docker daemon. Keep the production image build
# deterministic; users can override this at build time if they have more RAM.
ENV CMAKE_BUILD_PARALLEL_LEVEL=2
ARG MIOS_BUILD_TESTING=ON
WORKDIR /ws

RUN apt-get update && apt-get install -y --no-install-recommends \
      git python3-pip python3-rosdep python3-vcstool libpoco-dev nlohmann-json3-dev \
      ros-jazzy-controller-manager ros-jazzy-ros2-control \
      ros-jazzy-joint-state-broadcaster ros-jazzy-xacro

# Keep apt indices for rosdep below. They are cleaned after dependency
# resolution rather than before rosdep invokes apt-get.

# Pin only the upstream packages required for the hardware path. The complete
# dependency.repos also brings Gazebo, ZED, and vision packages, which are
# deliberately excluded from this no-MoveIt/no-simulation image.
# The upstream Noble libfranka package matches the Franka Jazzy dependency pin
# and avoids building libfranka's test targets inside this runtime image.
RUN mkdir -p src \
    && git clone https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
    && git -C src/franka_ros2 checkout ee1b79b77e473751852b4f884d1f7ce86041dfff \
    && git clone --branch 2.8.1 --depth 1 https://github.com/frankarobotics/franka_description.git src/franka_description \
    # franka_bringup is also the real-hardware launch package, but upstream
    # declares optional simulation, mobile, and example-controller packages
    # as workspace dependencies.  Remove those optional dependencies so the
    # FR3 hardware path can be built without Gazebo or MoveIt 2.
    && sed -i -E '/franka_(gazebo|mobile|example|vision_and_manipulation_kit)/d' src/franka_ros2/franka_bringup/package.xml \
    && curl --fail --location --output /tmp/libfranka.deb \
         https://github.com/frankarobotics/libfranka/releases/download/0.20.5/libfranka_0.20.5_noble_amd64.deb \
    && dpkg --install /tmp/libfranka.deb \
    && rm /tmp/libfranka.deb \
    && rosdep update \
    && rosdep install --ignore-src --rosdistro jazzy -y \
         --skip-keys="ament_cmake_clang_format xacro libfranka" \
         --from-paths src/franka_ros2/franka_hardware \
                      src/franka_ros2/franka_msgs \
                      src/franka_ros2/franka_semantic_components \
                      src/franka_description \
    && rm -rf /var/lib/apt/lists/*

COPY mios/docker/ros2/franka_combined_control.patch /tmp/franka_combined_control.patch
RUN git -C /ws/src/franka_ros2 apply --check /tmp/franka_combined_control.patch \
    && git -C /ws/src/franka_ros2 apply /tmp/franka_combined_control.patch \
    && rm /tmp/franka_combined_control.patch

# Jazzy's installed 4.45.2 binaries do not provide the hardware-synchronized
# loop. Build 4.47.0 and every loaded consumer of its interfaces in one overlay.
# Verify immutable commits as well as release tags, including the CMake support
# package. Keep the broadcaster at its existing 4.40.1 release, but rebuild it
# against the new controller_interface/hardware_interface ABI.
# Exclude Franka's vendored realtime_tools 3.10.1: retain the installed 3.11.0
# implementation rather than silently downgrading it through dependency discovery.
RUN touch src/franka_ros2/realtime_tools/COLCON_IGNORE \
    && git clone --branch 4.47.0 --depth 1 https://github.com/ros-controls/ros2_control.git src/ros2_control \
    && test "$(git -C src/ros2_control rev-parse HEAD)" = df23a4b7a21cb8ea257c80ecf98e85571b50ba01 \
    && git clone --branch 0.4.0 --depth 1 https://github.com/ros-controls/ros2_control_cmake.git src/ros2_control_cmake \
    && test "$(git -C src/ros2_control_cmake rev-parse HEAD)" = 929a94a169b4a6255edf27dd19c694ca20092686 \
    && git clone --branch 4.40.1 --depth 1 https://github.com/ros-controls/ros2_controllers.git src/ros2_controllers \
    && test "$(git -C src/ros2_controllers rev-parse HEAD)" = 31015e0aa7ce9d0853a88d5fc2fe50f0e583ba5c \
    && source /opt/ros/jazzy/setup.bash \
    && apt-get update \
    && rosdep install --ignore-src --rosdistro jazzy -y \
         --from-paths $(colcon list \
           --packages-up-to ros2_control joint_state_broadcaster hardware_interface_testing \
           --paths-only) \
    && rm -rf /var/lib/apt/lists/* \
    && colcon build --symlink-install --executor sequential --parallel-workers 1 \
         --packages-up-to ros2_control joint_state_broadcaster hardware_interface_testing \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF

# Compile only the upstream synchronization-policy regression test. Do not
# install its test controllers or build the rest of the upstream test suite.
# Run with: ctest --test-dir /ws/build/controller_manager \
#              -R '^test_sleeping_policies$' --output-on-failure
RUN if [ "${MIOS_BUILD_TESTING}" = "ON" ]; then \
      source /opt/ros/jazzy/setup.bash \
      && source /ws/install/setup.bash \
      && cmake -S /ws/src/ros2_control/controller_manager \
           -B /ws/build/controller_manager -DBUILD_TESTING=ON \
      && cmake --build /ws/build/controller_manager --target test_sleeping_policies; \
    fi

COPY mios/ros2_ws/src/mios_msgs /ws/src/mios_msgs
COPY mios/ros2_ws/src/mios_ros2_control /ws/src/mios_ros2_control
COPY mios/ros2_ws/src/mios_ros2_runtime /ws/src/mios_ros2_runtime
# The runtime uses this contract to consume commands from the original MIOS
# algorithms. It is data-only and contains no FCI/libfranka dependency.
COPY mios/src/utils/include/mios/control /ws/src/mios_control_types/include/mios/control
# These are small, neutral Core interface contracts only. They contain no
# vendor SDK include or FCI ownership.
COPY mios/src/core/include/mios/core/robot_backend.hpp /ws/src/mios_core_contract/include/mios/core/robot_backend.hpp
COPY mios/src/utils/include/mios/utils/types.hpp /ws/src/mios_core_contract/include/mios/utils/types.hpp

# Rebuild all Franka and MIOS plugins against the pinned ros2_control overlay.
# Sourcing it first also records the overlay for downstream package discovery.
RUN source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && colcon build --symlink-install --executor sequential --parallel-workers 1 \
         --packages-select \
           forward_command_controller \
           franka_description \
           franka_msgs \
           franka_semantic_components \
           franka_hardware \
           franka_robot_state_broadcaster \
           franka_gripper \
           franka_bringup \
           mios_msgs \
           mios_ros2_control \
           mios_ros2_runtime \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF

# Build MIOS-only CTest executables without enabling the upstream Franka test
# suites. These tests run with --network none in the validation command.
RUN if [ "${MIOS_BUILD_TESTING}" = "ON" ]; then \
      source /opt/ros/jazzy/setup.bash \
      && source /ws/install/setup.bash \
      && colcon build --symlink-install --executor sequential --parallel-workers 1 \
           --packages-select mios_ros2_control mios_ros2_runtime \
           --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON; \
    fi

# Keep the Portal teaching entry point available inside the image as well.
COPY mios/python/mios_examples.py /opt/mios/python/mios_examples.py
COPY mios/python/utils/ws_client.py /opt/mios/python/utils/ws_client.py
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-websockets \
    && rm -rf /var/lib/apt/lists/*

COPY mios/docker/ros2/entrypoint.sh /entrypoint.sh
COPY mios/docker/ros2/start_model_broadcaster.sh /usr/local/bin/start_model_broadcaster.sh
RUN chmod +x /entrypoint.sh
RUN chmod +x /usr/local/bin/start_model_broadcaster.sh

# Keep gripper recovery independent of the expensive arm/controller build.
# Failed reads must not republish stale width; bounded respawn reconnects only
# the gripper node, without homing or replaying any physical command.
COPY mios/docker/ros2/franka_gripper_recovery.patch /tmp/franka_gripper_recovery.patch
RUN git -C /ws/src/franka_ros2 apply --check /tmp/franka_gripper_recovery.patch \
    && git -C /ws/src/franka_ros2 apply /tmp/franka_gripper_recovery.patch \
    && rm /tmp/franka_gripper_recovery.patch \
    && source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && colcon build --symlink-install --executor sequential --parallel-workers 1 \
         --packages-select franka_gripper \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF
COPY mios/docker/ros2/start_control.sh /usr/local/bin/start_control.sh
COPY mios/docker/ros2/check_control_ready.sh /usr/local/bin/check_control_ready.sh
RUN chmod +x /usr/local/bin/start_control.sh /usr/local/bin/check_control_ready.sh
HEALTHCHECK --interval=5s --timeout=2s --start-period=70s --retries=3 \
  CMD ["/usr/local/bin/check_control_ready.sh"]
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/start_control.sh"]
