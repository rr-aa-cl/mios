# ROS-only MIOS deployment

This deployment uses `franka_hardware` as the **only** FCI client.  The MIOS
Core runs separately with `Ros2CoreRobotBackend`, communicates through ROS 2
topics/actions, and retains the existing MIOS Portal at port `12000`. It never
constructs a vendor SDK client.

## Layout

```
docker/
  docker-bake.hcl      builds the three images in one command
  compose.yml          Docker Compose deployment
  common/              entrypoint.sh (ROS environment) and runtime_lib.sh
                       (CPU pinning, waiting for ports), used by Control and Core
  control/             Dockerfile, start_control.sh, prepare_controllers.sh,
                       check_control_ready.sh, patches/ (franka_ros2, ros2_control)
  core/                Dockerfile, start_core.sh, check_core_ready.sh
  ml_service/          Dockerfile, mls_runtime.py (start | probe | stop)
  k8s/                 kustomization.yaml, runtime.yml, runtime.env, MongoDB
  host/                files installed on the robot PC itself (NIC IRQ pinning)
```

## How the services start

Each image carries its own start script and runs it by default. Docker Compose
and Kubernetes run the same script; neither wraps it.

| Service | Start | Ready when |
|---|---|---|
| Control | `start_control.sh` launches `franka_bringup`, then `prepare_controllers.sh` loads the arm controllers (inactive) and activates the model broadcaster | `check_control_ready.sh`: preparation finished and the launch is alive |
| Core | `start_core.sh` starts `mios_ros2_core_runtime` | `check_core_ready.sh`: the Portal port accepts a connection |
| MLS | `mls_runtime.py start` supervises `start_interface.py` | `mls_runtime.py probe`: the service owns its two listening ports |

Start order is Control, then Core, then MLS; shutdown is the reverse.

The arm is controllable only while a task runs. Core starts with
`mios_effort_controller` inactive, activates it with the first arm skill of a
task and deactivates it when the task ends. In between the robot is in Franka
IDLE mode: it holds its position itself and command topics have no effect.

Settings are environment variables. The defaults live in the start scripts.
Compose repeats them in `compose.yml` so they can be overridden; the
Kubernetes deployment sets them in `k8s/runtime.env`. Steps that Compose does
with its own keys are requested through the environment on Kubernetes:

| Variable | Used by | Effect |
|---|---|---|
| `MIOS_REQUIRE_RT_LIMITS=true` | Control | raise and require rtprio 99 and unlimited memlock (Compose: `ulimits`) |
| `MIOS_CONTROL_RT_CPU` | Control | require the worker CPUs plus this CPU to be available |
| `MIOS_FCI_LOCK_FILE` | Control | hold a node-local lock so only one Control owns the robot |
| `MIOS_NONRT_CPUS` | Core, MLS | pin the service to these CPUs (Compose: `cpuset`) |
| `MIOS_STARTUP_WAIT_SECONDS` | Core, MLS | wait for MongoDB (and, for MLS, the Core Portal) |

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

To build all three images together without naming the Control image at all,
use bake. Core then takes its ROS overlay from the Control build of the same
run:

```bash
TAG=latest docker buildx bake -f docker/docker-bake.hcl --allow=fs.read=..
```

`REPO` (default `janine86`) and `TAG` (default `latest`) set the image names
(`ros2-control`, `ros2-core`, `mls`);
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
docker compose -f docker/compose.yml build ros2_control
docker compose -f docker/compose.yml build ros2_core mls
docker compose -f docker/compose.yml up -d
docker compose -f docker/compose.yml logs -f ros2_control
```

### Deploy on Kubernetes

Set the image names and tags in `docker/k8s/kustomization.yaml` and the
settings in `docker/k8s/runtime.env`, then:

```bash
kubectl apply -k docker/k8s
kubectl logs -f -n nuc3 deploy/mios-runtime -c control
```

Editing `runtime.env` changes the generated ConfigMap's name, which replaces
the Pod on the next apply.
