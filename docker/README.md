# ROS-only MIOS deployment

This deployment uses `franka_hardware` as the **only** FCI client.  The MIOS
Core runs separately with `Ros2CoreRobotBackend`, communicates through ROS 2
topics/actions, and retains the existing MIOS Portal at port `12000`. It never
constructs a vendor SDK client.

## Build and start the stack

### libfranka version and Ubuntu package

Control pins **libfranka 0.21.1** using
`libfranka_0.21.1_noble_amd64.deb`, with SHA-256 verification. This matches
the image's **Ubuntu 24.04 (Noble) / ROS 2 Jazzy** base. The
`libfranka_0.21.1_jammy_amd64.deb` package targets Ubuntu 22.04 and depends on
`libfmt.so.8`; the Noble build uses `libfmt.so.9`.

The robot's **System 5.9.2** belongs to the protocol-10 generation supported
by libfranka 0.21.1. See the upstream
[compatibility table](https://frankarobotics.github.io/docs/compatibility.html)
and [0.21.1 release packages](https://github.com/frankarobotics/libfranka/releases/tag/0.21.1).

Rebuild Control so its Franka driver and MIOS plugins link against the new
`libfranka.so.0.21`. Then rebuild Core against that Control image to refresh
its copied ROS workspace artifacts. Installing the package into an existing
container does not rebuild those consumers. The Dockerfile pin affects new
image builds; it does not update a running deployment.

### Build Control directly with Docker

From the repository root (the checkout directory must be named `mios`):

```bash
docker build -f docker/control/Dockerfile -t xxx/ros2-control:latest ..
docker build -f docker/core/Dockerfile -t xxx/ros2-core:latest ..
docker build -f docker/mls/Dockerfile -t xxx/mls:latest .
```

The final `..` selects the repository's parent as the build context. Control's
Dockerfile uses `COPY mios/...` paths relative to that context. Using `.` here
causes `COPY` checksum or "not found" errors even when the files exist in the
checkout.

Core also requires the parent context (`..`). When building Core against the
Control tag above, pass
`--build-arg MIOS_CONTROL_IMAGE=janine86/ros2-control:latest`.
The MLS Dockerfile uses the repository root context (`.`). The Compose
configuration below already selects the correct context for each image.

### Build and start with Compose

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ros2_control
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ros2_core mios_ml_service
docker compose -f docker/ros2/docker-compose.runtime.yml up -d
docker compose -f docker/ros2/docker-compose.runtime.yml logs -f mios_ros2_control
```