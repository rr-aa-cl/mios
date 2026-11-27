# syntax=docker/dockerfile:1

# Two stages:
#   build    compilers, sources, build trees and (optionally) the test binaries
#   runtime  the default target: ROS runtime packages, libfranka's shared
#            library and the /ws/install overlay only
#
# Build context is the parent directory of the `mios` checkout:
#   docker build -f docker/control/Dockerfile -t <repo>/ros2-control:latest ..
# Test binaries live only in the build stage:
#   docker build -f docker/control/Dockerfile --target build \
#     --build-arg MIOS_BUILD_TESTING=ON -t <repo>/ros2-control:build ..

ARG MIOS_CORE_CONTRACT_VERSION=0.1.0

###############################################################################
FROM ros:jazzy-ros-base AS build

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ARG MIOS_BUILD_TESTING=OFF
# colcon runs one package at a time and gives make every CPU. Set this to a
# number (for example 4) when the Docker daemon has little memory.
ARG MIOS_BUILD_JOBS=""
ENV CCACHE_DIR=/root/.cache/ccache \
    CCACHE_MAXSIZE=5G \
    CCACHE_BASEDIR=/ws
WORKDIR /ws

# Keep downloaded .deb files and package indices in BuildKit cache mounts, so
# a rebuilt layer does not download them again and none of it enters a layer.
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      ccache git libpoco-dev nlohmann-json3-dev \
      ros-jazzy-controller-manager ros-jazzy-ros2-control \
      ros-jazzy-joint-state-broadcaster ros-jazzy-xacro

# Use the Noble libfranka build for this Ubuntu 24.04/Jazzy base. The Jammy
# package requires a different libfmt ABI. Rebuild all consumers below when
# changing libfranka, because its shared-library SONAME includes the minor version.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    curl --fail --location --retry 10 --retry-all-errors --retry-delay 5 --connect-timeout 30 --max-time 300 --output /tmp/libfranka.deb \
         https://github.com/frankarobotics/libfranka/releases/download/0.21.1/libfranka_0.21.1_noble_amd64.deb \
    && echo 'bdab2485e91b23094140f5d13a262570f34371e5d4c22bfe537ff0503466b7c2  /tmp/libfranka.deb' | sha256sum --check --strict \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/libfranka.deb \
    && rm /tmp/libfranka.deb

# Pin only the upstream packages required for the hardware path. The complete
# dependency.repos also brings Gazebo, ZED, and vision packages, which are
# deliberately excluded from this no-MoveIt/no-simulation image.
# Both patches are applied here, before anything is compiled, so each Franka
# package is built exactly once.
COPY mios/docker/control/patches/franka_combined_control.patch mios/docker/control/patches/franka_gripper_recovery.patch /tmp/patches/
RUN mkdir -p src/franka_ros2 \
    && git -C src/franka_ros2 init --quiet \
    && git -C src/franka_ros2 fetch --depth 1 https://github.com/frankarobotics/franka_ros2.git ee1b79b77e473751852b4f884d1f7ce86041dfff \
    && git -C src/franka_ros2 checkout --quiet FETCH_HEAD \
    && git clone --branch 2.8.1 --depth 1 https://github.com/frankarobotics/franka_description.git src/franka_description \
    # franka_bringup is also the real-hardware launch package, but upstream
    # declares optional simulation, mobile, and example-controller packages
    # as workspace dependencies.  Remove those optional dependencies so the
    # FR3 hardware path can be built without Gazebo or MoveIt 2.
    && sed -i -E '/franka_(gazebo|mobile|example|vision_and_manipulation_kit)/d' src/franka_ros2/franka_bringup/package.xml \
    && for patch in franka_combined_control franka_gripper_recovery; do \
         git -C src/franka_ros2 apply --check /tmp/patches/${patch}.patch \
         && git -C src/franka_ros2 apply /tmp/patches/${patch}.patch || exit 1; \
       done \
    # Exclude Franka's vendored realtime_tools 3.10.1: retain the installed
    # 3.11.0 implementation rather than silently downgrading it through
    # dependency discovery.
    && touch src/franka_ros2/realtime_tools/COLCON_IGNORE

# Jazzy's installed 4.45.2 binaries do not provide the hardware-synchronized
# loop. Build 4.47.0 and every loaded consumer of its interfaces in one overlay.
# Verify immutable commits as well as release tags, including the CMake support
# package. Keep the broadcaster at its existing 4.40.1 release, but rebuild it
# against the new controller_interface/hardware_interface ABI.
COPY mios/docker/control/patches/controller_manager_deactivate_switch.patch /tmp/patches/
COPY mios/docker/control/patches/test_controller_manager_deactivate_switch.cpp /tmp/patches/
RUN git clone --branch 4.47.0 --depth 1 https://github.com/ros-controls/ros2_control.git src/ros2_control \
    && test "$(git -C src/ros2_control rev-parse HEAD)" = df23a4b7a21cb8ea257c80ecf98e85571b50ba01 \
    && git -C src/ros2_control apply --check /tmp/patches/controller_manager_deactivate_switch.patch \
    && git -C src/ros2_control apply /tmp/patches/controller_manager_deactivate_switch.patch \
    && cp /tmp/patches/test_controller_manager_deactivate_switch.cpp src/ros2_control/controller_manager/test/ \
    && git clone --branch 0.4.0 --depth 1 https://github.com/ros-controls/ros2_control_cmake.git src/ros2_control_cmake \
    && test "$(git -C src/ros2_control_cmake rev-parse HEAD)" = 929a94a169b4a6255edf27dd19c694ca20092686 \
    && git clone --branch 4.40.1 --depth 1 https://github.com/ros-controls/ros2_controllers.git src/ros2_controllers \
    && test "$(git -C src/ros2_controllers rev-parse HEAD)" = 31015e0aa7ce9d0853a88d5fc2fe50f0e583ba5c

# Install what is needed to compile, and nothing else. The test and exec
# dependencies of these packages include clang-tidy/LLVM, rviz2 and Qt (about
# 1.9 GB); they are only installed when the test binaries are requested.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    source /opt/ros/jazzy/setup.bash \
    && if [ "${MIOS_BUILD_TESTING}" = "ON" ]; then types=(); \
       else types=(-t build -t buildtool -t build_export -t buildtool_export); fi \
    && rosdep update --rosdistro jazzy \
    && apt-get update \
    && rosdep install --ignore-src --rosdistro jazzy -y "${types[@]}" \
         --skip-keys="ament_cmake_clang_format xacro libfranka" \
         --from-paths src/franka_ros2/franka_hardware \
                      src/franka_ros2/franka_msgs \
                      src/franka_ros2/franka_semantic_components \
                      src/franka_description \
                      $(colcon list \
                        --packages-up-to ros2_control joint_state_broadcaster hardware_interface_testing \
                        --paths-only)

# Plain (copying) installs keep /ws/install self-contained, so later stages
# and the Core image need neither /ws/build nor /ws/src.
RUN --mount=type=cache,target=/root/.cache/ccache \
    source /opt/ros/jazzy/setup.bash \
    && if [ -n "${MIOS_BUILD_JOBS}" ]; then export MAKEFLAGS="-j${MIOS_BUILD_JOBS}"; fi \
    && colcon build --executor sequential --parallel-workers 1 \
         --packages-up-to ros2_control joint_state_broadcaster hardware_interface_testing \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF \
           -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

# Compile the synchronization-policy, deactivation, and activity lifecycle
# regressions. Do not install their test controllers or build the full suite.
# Run with: ctest --test-dir /ws/build/controller_manager \
#   -R '^(test_sleeping_policies|test_controller_manager_deactivate_switch|test_controller_manager_hardware_error_handling)$' --output-on-failure
# Activity lifecycle: /ws/build/controller_manager/test_controller_manager \
#   --gtest_filter='*controller_lifecycle*'
RUN --mount=type=cache,target=/root/.cache/ccache \
    if [ "${MIOS_BUILD_TESTING}" = "ON" ]; then \
      source /opt/ros/jazzy/setup.bash \
      && source /ws/install/setup.bash \
      && cmake -S /ws/src/ros2_control/controller_manager \
           -B /ws/build/controller_manager -DBUILD_TESTING=ON \
      && cmake --build /ws/build/controller_manager --parallel ${MIOS_BUILD_JOBS:-$(nproc)} --target \
           test_sleeping_policies test_controller_manager_deactivate_switch \
           test_controller_manager_hardware_error_handling test_controller_manager; \
    fi

# Rebuild the Franka plugins against the pinned ros2_control overlay. This
# layer does not depend on any MIOS source, so editing MIOS code reuses it.
# Sourcing the overlay first also records it for downstream package discovery.
RUN --mount=type=cache,target=/root/.cache/ccache \
    source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && if [ -n "${MIOS_BUILD_JOBS}" ]; then export MAKEFLAGS="-j${MIOS_BUILD_JOBS}"; fi \
    && colcon build --executor sequential --parallel-workers 1 \
         --packages-select \
           forward_command_controller \
           franka_description \
           franka_msgs \
           franka_semantic_components \
           franka_hardware \
           franka_robot_state_broadcaster \
           franka_gripper \
           franka_bringup \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF \
           -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    # ros2_control and robot_state_publisher only read the URDF text. The
    # visual and collision meshes (190 MB) are never opened on the robot PC;
    # a remote RViz resolves package://franka_description on its own machine.
    && rm -rf /ws/install/franka_description/share/franka_description/meshes

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

# Only these three packages are recompiled when MIOS sources change.
RUN --mount=type=cache,target=/root/.cache/ccache \
    source /opt/ros/jazzy/setup.bash \
    && source /ws/install/setup.bash \
    && if [ -n "${MIOS_BUILD_JOBS}" ]; then export MAKEFLAGS="-j${MIOS_BUILD_JOBS}"; fi \
    && colcon build --executor sequential --parallel-workers 1 \
         --packages-select mios_msgs mios_ros2_control mios_ros2_runtime \
         --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF \
           -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    # Build MIOS-only CTest executables without enabling the upstream Franka
    # test suites. These tests run with --network none in the validation command.
    && if [ "${MIOS_BUILD_TESTING}" = "ON" ]; then \
         colcon build --executor sequential --parallel-workers 1 \
           --packages-select mios_ros2_control mios_ros2_runtime \
           --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON \
             -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache; \
       fi

###############################################################################
FROM ros:jazzy-ros-core AS runtime

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG MIOS_CORE_CONTRACT_VERSION
LABEL org.opencontainers.image.title="mios-ros2-control" \
      io.mios.core-contract.version="${MIOS_CORE_CONTRACT_VERSION}"
ENV DEBIAN_FRONTEND=noninteractive
ENV RCUTILS_CONSOLE_OUTPUT_FORMAT="[{date_time_with_ms}] [{severity}] [{name}]: {message}"
WORKDIR /ws

# Runtime dependencies only. The ros2_control and broadcaster packages are
# installed for their dependency closure; the 4.47.0 overlay in /ws/install
# takes precedence over their 4.45.2 binaries. libfranka's .deb depends on
# -dev packages, so its shared library is copied and only the libraries it
# actually links are installed here.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libfmt9 libpocofoundation80t64 libpoconet80t64 python3-websockets \
      ros-jazzy-ros2-control \
      ros-jazzy-joint-state-broadcaster ros-jazzy-forward-command-controller \
      ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher \
      ros-jazzy-xacro ros-jazzy-urdf \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/lib/libfranka.so.0.21.1 /usr/lib/
RUN ldconfig
COPY --from=build /ws/install /ws/install

# Keep the Portal teaching entry point available inside the image as well.
COPY mios/python/mios_examples.py /opt/mios/python/mios_examples.py
COPY mios/python/utils/ws_client.py /opt/mios/python/utils/ws_client.py

COPY --chmod=755 mios/docker/common/entrypoint.sh /entrypoint.sh
COPY mios/docker/common/runtime_lib.sh /usr/local/lib/mios/runtime_lib.sh
COPY --chmod=755 mios/docker/control/start_control.sh \
                 mios/docker/control/prepare_controllers.sh \
                 mios/docker/control/check_control_ready.sh /usr/local/bin/

HEALTHCHECK --interval=5s --timeout=2s --start-period=70s --retries=3 \
  CMD ["/usr/local/bin/check_control_ready.sh"]
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/start_control.sh"]
