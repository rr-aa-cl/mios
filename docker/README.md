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


### Build Control directly with Docker

From the repository root (the checkout directory must be named `mios`):

```bash
docker build -f docker/control/Dockerfile -t xxx/ros2-control:latest ..
docker build -f docker/core/Dockerfile -t xxx/ros2-core:latest \
  --build-arg MIOS_CONTROL_IMAGE=xxx/ros2-control:latest ..
docker build -f docker/ml_service/Dockerfile -t xxx/mls:latest .
```

To build Control and Core together without naming the Control image at all,
use bake. Core then takes its ROS overlay from the Control build of the same
run:

```bash
TAG=latest docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=..
```

`REPO` (default `janine86`) and `TAG` (default `latest`) set both image names;
add `--push` to push them. `docker compose ... build ros2_core` links the two
builds the same way.

Both Dockerfiles are multi-stage. The default target is a slim `runtime`
stage without compilers, sources or build trees; the `build` stage keeps them.
Core copies `/ws/install` out of the Control image, so build Control first and
pass its tag as `MIOS_CONTROL_IMAGE`.

Useful build arguments for Control:

- `--build-arg MIOS_BUILD_JOBS=4` limits make to four jobs when the Docker
  daemon has little memory (default: all CPUs).
- `--target build --build-arg MIOS_BUILD_TESTING=ON` produces an image with the
  controller-manager and MIOS test binaries in `/ws/build`.

Compiler output is kept in a BuildKit ccache mount, so a rebuild after a
source change recompiles only what changed.

The final `..` selects the repository's parent as the build context. Control's
Dockerfile uses `COPY mios/...` paths relative to that context. Using `.` here
causes `COPY` checksum or "not found" errors even when the files exist in the
checkout.
Core also requires the parent context (`..`). 

### Build and start with Compose

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml build ros2_control
docker compose -f docker/ros2/docker-compose.runtime.yml build ros2_core mls
docker compose -f docker/ros2/docker-compose.runtime.yml up -d
docker compose -f docker/ros2/docker-compose.runtime.yml logs -f ros2_control
```