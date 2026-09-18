# ROS-only MIOS deployment

This deployment uses `franka_hardware` as the **only** FCI client.  The MIOS
Core runs separately with `Ros2CoreRobotBackend`, communicates through ROS 2
topics/actions, and retains the existing MIOS Portal at port `12000`. It never
constructs a vendor SDK client.

## Check readiness before deployment

After building the Control, Core, and ML images, run this command once for
the intended deployment profile, from the repository root on the Linux
deployment host with Python 3.10 or newer. Use the same exported image
selection when launching Compose:

```bash
python3 tools/check_deployment_ready.py \
  --profile motion \
  --json build/readiness.json
```

Choose the profile in that command:

- `motion` (default): checks the teaching/learning configuration used by plain
  Compose startup. The gripper, Core scheduler, task execution, and
  controller-owned Move settings default to `true`; no exports are needed.
  This profile also checks the installed effort-controller gates and the
  commissioned power policy, rejecting powersave or enabled idle states
  above 1 us.
- `state-only`: checks a deployment with the Core Portal available and robot
  task execution disabled. Export `MIOS_ENABLE_CORE_TASK_EXECUTION=false` and
  `MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE=false` before checking with this
  profile and launching Compose. Keep `MIOS_ENABLE_CORE_SCHEDULER=true`.
  `MIOS_LOAD_GRIPPER=false` also disables the gripper node if desired.

The tool inspects the resolved Compose configuration and local images, then
reports `PASS`, `WARN`, `FAIL`, or `UNKNOWN` with suggested fixes. It needs
Docker/Compose, `ip` and `ss` from iproute2, `ethtool`, `ps`, and `ping`.
Python's standard library is sufficient on the host. Candidate images must
already exist locally; the checker does not build or pull them.

Checks cover:

- PREEMPT_RT, online/isolated CPUs, SMT sibling exclusion, and worker placement.
- CPU governor/deep-idle settings, the direct Gigabit Ethernet link, NIC IRQ
  affinity/priority, NIC tuning, and five ICMP reachability probes.
- Docker access, native architecture, storage, Compose networking/IPC,
  scheduling permissions, consistent ROS domains, and task gates.
- Actual ros2_control version and synchronization support, installed YAML,
  plugin dependency resolution, Core contract labels and vendor-library
  separation, image startup scripts, and ML Python dependencies and taxonomy.
- Existing FCI owners/connections, occupied Core/ML ports, and a reachable
  local Mongo dependency port. Mongo credentials and schema are not checked.

Image inspections run in uniquely named disposable containers with networking
disabled, a read-only filesystem, all capabilities dropped, and the service
entrypoint replaced. The checker does not open FCI, activate controllers,
change host settings, or stop running services. It removes its own probe
containers even if interrupted. `--no-ping` also suppresses ICMP probes and
records a warning.

This is a pre-deployment check, so a running Control container or occupied
service ports blocks replacement. Complete the supervised shutdown of an
existing stack before expecting a passing report. Keep the separately managed
Mongo service available. The tool inspects the Control, Core, and MLS
Compose services, their selected images, and the planned service ports.

Exit status is **0** when all required checks pass, **1** for failures or
unknown required checks, and **2** for argument/report-writing errors.
Warnings do not block by default; `--strict` makes them blockers. Use
`--quiet` to show only problems and the final result. A report is a timestamped
snapshot of the host and inspected image IDs. It cannot prove FCI deadlines,
robot-side FCI enablement, physical workspace readiness, or a successful task;
retain the offline tests and supervised transport validation below.

Proceed to the launch commands below only after the checker exits with
status **0**, using the same image selection and task-gate environment.

`--control-image`, `--core-image`, and `--robot-ip` affect this inspection's
Compose resolution only; reuse their matching environment settings when you
deploy. `--ml-image` overrides `MIOS_ML_SERVICE_IMAGE` for the inspection;
reuse that image selection when deploying. Runtime mounts,
entrypoint overrides, and alternative shell command forms are reported as
unverified, since they can replace the files inspected inside an image.

The regression tests run offline without Docker or robot hardware:

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py' -v
```

## Build and start the stack

From the repository root, with the separately managed MongoDB service
available on the deployment host:

If MLS was previously started with `docker run`, complete the one-time
[MLS migration](#run-the-ml-service-in-docker) before the first `up -d`.

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ros2_control
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ros2_core mios_ml_service
docker compose -f docker/ros2/docker-compose.runtime.yml up -d
docker compose -f docker/ros2/docker-compose.runtime.yml logs -f mios_ros2_control
```

The plain `up -d` command starts **Control, Core, and MLS** together. Control
runs its preparation helper inside the container on every start. It starts
the read-only model broadcaster and configures the effort and joint-position
controllers as `inactive`. Control becomes healthy after preparation; Core
then waits for fresh feedback before opening the Portal. No Compose profile
is required. The Core
scheduler starts the Portal on port `12000`; the gripper and Core task settings
are enabled for the teaching/learning examples. These defaults survive
container recreation and new shells. Startup leaves the arm controllers
inactive and does not run an example or close the gripper. MongoDB remains
separately managed.

If the Core container is `Up` but port `12000` refuses connections, check
`docker compose -f docker/ros2/docker-compose.runtime.yml logs mios_ros2_core`.
`MIOS_ENABLE_CORE_SCHEDULER=false` selects a construction test that never
opens the Portal. Remove that override or export it as `true`, then run
`up -d` again. Core also needs MongoDB and fresh ROS state/model messages
before the Portal can open.

### Gripper disconnects while Control stays running

Control contains separate arm and gripper processes. Docker can report it as
`Up` after `franka_gripper_node` has crashed. Check the gripper's own log and
ROS action server:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml logs mios_ros2_control 2>&1 | rg 'franka_gripper|UDP receive|process has died'
docker exec mios-ros2-control bash -lc 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && ros2 action info /franka_gripper/grasp --count'
```

Logs are retained across container restarts. `logs -f` prints that history
before following new output, so an old timeout can appear again after every
restart. To inspect only the current Control run:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml logs -f --timestamps \
  --since "$(docker inspect --format '{{.State.StartedAt}}' mios-ros2-control)" mios_ros2_control
```

Expect exactly one action server. `libfranka: UDP receive: Timeout` followed
by `Poco::Net::NetException` and a process exit means the gripper driver lost
communication and crashed; rebuilding the same unpatched driver does not
add recovery. The Control image applies `franka_gripper_recovery.patch`:
failed state reads end the process before an old width can be published with
a new timestamp, and ROS launch retries only the gripper process up to five
times with a two-second delay. Reconnecting does not home, open, close, or
replay an interrupted command. Persistent connection failures still require
diagnosing the robot/network; retries do not repair that underlying cause.
If a timeout is followed by `Connected to gripper` and fresh state feedback,
the retry restored communication. The error remains in the logs; rebuilding
again does not diagnose the original packet interruption.

After rebuilding Control, run `docker compose -f docker/ros2/docker-compose.runtime.yml up -d` to recreate the container with
the new image. A Docker restart alone keeps the existing image. The image
readiness check verifies the recovery code and launch settings; the example
preflight requires a live action server and fresh gripper feedback.

## Synchronize the control loop with Franka

The Control image builds ros2_control 4.47.0 and rebuilds its dependent
controllers against the same interfaces. The hardware configuration enables
`hardware_synchronization.expect_blocking_read_write`: Franka's blocking
read paces the read/update/write loop at the robot's 1 kHz rate. This prevents
the host's separate periodic timer from drifting relative to incoming robot
states. The parameter requires ros2_control 4.47.0 or newer; adding it to an
older image does not enable synchronization.

Keep `update_rate: 1000` and the existing activation gates and effort limits.
The upstream minimum-cycle guard remains at its default for periods when the
hardware is inactive. GenericSystem tests disable hardware synchronization
because their reads return immediately.

Build and validate an isolated candidate while retaining the existing image:

```bash
MIOS_ROS2_CONTROL_IMAGE=mios-ros2-control:sync447 \
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ros2_control
docker run --rm --network none mios-ros2-control:sync447 bash -lc '
  source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash &&
  ctest --test-dir /ws/build/controller_manager -R "^test_sleeping_policies$" --output-on-failure &&
  ctest --test-dir /ws/build/mios_ros2_control --output-on-failure &&
  ctest --test-dir /ws/build/mios_ros2_runtime --output-on-failure
'
```

Before teaching, validate a bounded supervised controller session with an FCI
packet capture. Check response latency relative to matching robot-state IDs,
not just the outgoing packet frequency, and verify clean controller release.
Use the same `MIOS_ROS2_CONTROL_IMAGE` override when starting the candidate;
the existing `mios-ros2-control:local` image remains available for rollback.

## Real-time CPU placement

The FR3 FCI controller requires a 1 kHz communication loop.  The
controller-manager update thread itself is pinned to CPU 6 in
`mios_controllers.yaml`; all other threads in the FCI container inherit
`MIOS_CONTROL_WORKER_CPUS` (`0-5,8-19` by default). CPU 7 is the SMT sibling
of the reserved controller CPU 6 and is intentionally left idle; Core/MLS
containers use the same non-real-time set. On this commissioning host CPU 6
is reserved for the Franka Ethernet interrupt. Pin the actual NIC IRQ at boot
as well (the helper discovers the IRQ dynamically, so it does not rely on an
unstable PCI MSI number):

```bash
sudo install -m 0755 tools/pin_franka_nic_irq.sh /usr/local/sbin/mios-pin-franka-nic-irq
sudo install -m 0644 docker/ros2/mios-franka-nic-irq.service /etc/systemd/system/
sudo install -m 0644 docker/ros2/e1000e-franka.conf /etc/modprobe.d/e1000e-franka.conf
sudo systemctl daemon-reload
sudo systemctl enable --now mios-franka-nic-irq.service
```

The service disables EEE, Ethernet pause frames, and RX interrupt coalescing
on the dedicated Franka NIC before pinning its IRQ. The `e1000e` module
configuration disables dynamic interrupt throttling at the next host reboot.
Suspend/resume or a NIC driver reload can create a new IRQ and reset its
affinity/priority even while this one-shot service still reports active.
CPU power settings can also revert. Before starting Control after a reboot
or resume, restore the commissioned settings on this host:

```bash
sudo systemctl restart mios-franka-nic-irq.service
sudo cpupower -c 6,7 frequency-set -g performance
sudo cpupower -c 6,7 idle-set -D 2
```

The helper discovers the current IRQ. The CPU commands select the performance
governor and disable idle states with exit latency above 1 microsecond on the
reserved CPU pair. These host settings are independent of Docker images;
rebuilding or restarting containers does not restore them. The readiness
check at the top of this document verifies the resulting settings.

### Isolate the controller's physical CPU core

On this host CPU 7 is the SMT sibling of CPU 6, so reserve the whole physical
core. Add the following to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`,
run `sudo update-grub`, and reboot:

```text
isolcpus=managed_irq,domain,6-7 nohz_full=6-7 rcu_nocbs=6-7 irqaffinity=0-5,8-19
```

`irqaffinity` keeps ordinary IRQs off the reserved core. The
`mios-franka-nic-irq` service then pins only the Franka NIC IRQ back to CPU 6.
After boot, verify `cat /sys/devices/system/cpu/isolated` reports `6-7` and
that the NIC IRQ's `/proc/irq/<number>/smp_affinity_list` reports `6`.

If the Franka interface or reserved CPU changes, update the controller
manager's `cpu_affinity`, `MIOS_CONTROL_WORKER_CPUS`, `MIOS_NONRT_CPUS`, and
the IRQ service environment values together. Do **not** apply a Docker CPU
set to the whole FCI container: it would force libfranka's several FIFO-99
worker threads onto one CPU and can starve the controller-manager loop during
a mode switch. The Control startup `taskset` wrapper deliberately excludes only the
reserved CPU from ordinary FCI workers; `controller_manager` then assigns its
single update thread back to that CPU.
Do not raise the controller rate above 1 kHz or change controller priorities
while commissioning physical motion.

## Enable teaching and learning

The Compose file enables the gripper, Core scheduler, task execution, and
controller-owned Move support by default. With FCI enabled and MongoDB
available, start the stack from the repository root. Finish any active
teaching or learning session before updating an existing stack:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml up -d
```

No teaching exports are required, including after restarting the stack.
Existing environment or `.env` overrides still take precedence. If an older
configuration sets any of these options to `false`, remove that override or
set it to `true`: `MIOS_LOAD_GRIPPER`, `MIOS_ENABLE_CORE_SCHEDULER`,
`MIOS_ENABLE_CORE_TASK_EXECUTION`, `MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE`.
Run `up -d` to apply changed settings; `docker restart` and
`docker compose restart` reuse the old container configuration.

Core now owns controller activation through ROS services. It checks the
controller gates and exclusive ownership before each control call; the
controller checks live robot mode and stationary joints during activation.
Core releases the controller when that call finishes or fails. Teaching
waits for `control_active: true` before showing the hand-guiding prompt and
for idle afterward. With task execution enabled, Core requires fresh gripper
feedback; missing feedback cannot be used as a zero-width grasp reading.
Keep an operator supervising teaching/learning and follow the placement prompts.

`MIOS_ALLOW_ROBOT_PARAMETER_APPLICATION` must remain **false** for a
supervised task.  Franka parameter services (load, TCP, collision behaviour,
and stiffness) are not valid while an arm controller has the FCI in Move
mode.  Provision those values in Desk, or in a separately supervised Idle
configuration session before activating an arm command controller.

### Prepare controllers after a Control restart

Control runs controller preparation itself on every container start, including
`docker restart` or a replacement pod. It loads and configures
`mios_effort_controller` and `mios_joint_position_controller`, leaving both
inactive. Core activates the effort controller only for a task's control
call. No separate model container or laptop setup command is needed.

Rebuild Control, then Core and MLS using the commands under
[Build and start the stack](#build-and-start-the-stack), to deploy this change.
The client and Core must be updated together because teaching now reads
Core's `control_active` field.

With Core and MLS idle, check the current controller states:

```bash
docker exec mios-ros2-control bash --noprofile --norc -c '
  source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash &&
  ros2 control list_controllers -c /controller_manager
'
```

The expected result is `mios_effort_controller` and
`mios_joint_position_controller` both `inactive`. Setup does not claim arm
command interfaces or move the gripper. It refuses to take over an active
arm controller; finish that controller's owning session before rerunning
setup. If preparation fails, inspect the `mios_ros2_control` service logs.
Control exits on preparation failure instead of reporting readiness.

### Teach from the host or a laptop

Edit the function calls at the bottom of the two example files to choose the
Portal host and object name. The repository's existing `.venv` provides
their Python dependencies on this host. For a new checkout, use Python 3.11
or newer and install the dependencies declared in `ml_service/pyproject.toml`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ./ml_service
```

The examples need Python and network access to the service APIs. They do
not require a Docker CLI, Docker socket, ROS installation, or container name
on the laptop. Controller setup and ownership belong to the runtime.

The Control, Core, and MongoDB services must be ready, the gripper must be
enabled, and the effort controller must initially be inactive. Arm command
controllers must not already own the robot. The current call at the bottom
of `python/mios_examples.py` is:

```python
teach_insertion("127.0.0.1", "janinetest1", already_grasped=False)
```

With `already_grasped=False`, start with the fingers open. After the object
placement prompt, teaching follows this sequence:

1. Call `grasp` with width `0`, force `100` N, and requested speed `1` m/s.
   Since the object's width is unknown, contact is accepted throughout the
   usable gripper stroke. Wait for three settled width readings, spaced more
   than Core's 500 ms feedback-cache allowance apart.
2. Call `teach_object` with the insertable name, `width=True`, and `force=100`
   to save the grasp pose, measured width, and force.
3. Read `gripper_width` using `get_state`.
4. Prompt you to support the object from below or with a fixture, with fingers
   clear of the closing path. After Enter, call `move_gripper` with the measured
   width plus `0.005` m and requested speed `1` m/s. This opening can release
   the object. Type any text or press Ctrl+C to abort this prompt. Teaching
   stops if the target would exceed 80 mm.
5. Call `grasp_object` with the insertable name and speed `1` m/s. It uses the
   saved width and force. `move_gripper` itself has no force argument.

After the named grasp succeeds and its width passes the feedback checks,
teaching continues to the approach pose without an extra confirmation prompt.
Failed commands, zero/invalid readings, unsettled width, or width changes
during feedback verification stop the sequence.
Failure after `teach_object` leaves the grasp pose recorded, but the approach
and container poses are not taught in that run. No failed motion is retried
automatically.

A stable encoder opening alone does not establish that the object is held.
Readings at or below 1 mm trigger a message that an empty closure cannot be
excluded; feedback verification does not calibrate the width.

`TEACHING_GRASP_SPEED`, `TEACHING_GRASP_FORCE`, and
`TEACHING_REGRASP_CLEARANCE` near the top of `python/mios_examples.py` are the
fixed settings. Speed and force are passed to the gripper driver as requests;
they are not measurements of the achieved motion or force. The configured
force is saved with the grasp pose for subsequent object grasps.

Use `already_grasped=True` only when the object is already securely clamped.
It preserves that grasp and saves its pose after your confirmation; it does
not close the fingers. This mode also supports an operator-confirmed grasp
below 1 mm. An approximately 81 mm open-gripper reading is rejected as an
existing grasp.

From the repository root, run supervised teaching:

```bash
.venv/bin/python python/mios_examples.py
```

This starts the physical teaching workflow. Follow the grasp, approach,
insertion, and extraction prompts with an operator supervising the robot.
Core activates effort control for each hand-guiding task and releases it
when the task stops, before teaching saves the pose or advances.

The script runs from your local checkout, so local edits take effect without
rebuilding an image or copying the file into a container. It uses the Portal
for teaching and controller-readiness feedback.

The first function argument identifies the **Core Portal host**. On a
separate laptop, use the reachable address serving Core on port `12000`.
Controller-manager communication stays between Core and Control over ROS.

### Run the ML service in Docker

The ML service (MLS) is included in the default Compose startup alongside
Control and Core. Run these commands from the repository root on the
Linux deployment host, with MongoDB available at `127.0.0.1:27017` by default.

To build the image, or include recent service source changes, run this from
the repository root before creating the container:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml build mios_ml_service
```

MLS uses `MIOS_ML_SERVICE_IMAGE` (default `mios-ml-service:local`) and the
same `MIOS_NONRT_CPUS` set as Core. Its Core and MongoDB connection ports
follow `MIOS_WS_PORT` and `MONGO_PORT`.

If upgrading from a standalone `docker run` container named
`mios-ml-service`, first wait for MLS to be idle, then stop and preserve it
under a backup name before the first Compose startup:

```bash
docker stop mios-ml-service
docker rename mios-ml-service "mios-ml-service-standalone-$(date -u +%Y%m%dT%H%M%SZ)"
```

This migration is needed only once. Compose creates the replacement under
the original name; MongoDB and the stopped container's files are preserved.

Start the stack:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml up -d
```

The image automatically runs `python3 ./start_interface.py` from
`/mios_mls`. It listens on port `8000` for learning requests and port `8001`
for the knowledge database RPC service. Host networking also lets MLS reach
MongoDB on localhost.

View the service logs:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml logs -f mios_ml_service
```

Check that MLS responds:

```bash
python3 -c "from xmlrpc.client import ServerProxy; print(ServerProxy('http://127.0.0.1:8000').is_busy())"
```

`False` means MLS is reachable and idle. This check does not verify MongoDB
or robot readiness. Starting MLS does not launch a learning trial; Control
and Core must also be running before using the learning example below.

### Stop learning through the MLS API

For persistent `not in self.free_agents` or assigned-worker messages, see
[Diagnose an assigned learning agent](../docs/learning-agent-waits.md).

`stop_service()` on XML-RPC port `8000` cancels the current learning run;
the MLS server and container remain running so another run can be started.
It latches cancellation during initialization, stops the current Core task
with recovery disabled and its queue cleared, and prevents further setup,
trial, reset, or rescue commands. Paused learning cannot resume after a stop.

The updated method returns `True` when the stop request is acknowledged, or
`False` when a Core stop or optional command-loop shutdown could not be
confirmed. An RPC timeout also leaves the outcome unconfirmed; retry the
same method. Wait
for `is_busy()` to become `False` and for Core `get_state` to report
`status: Idle`, `current_task: IdleTask`, and `control_active: false` before
starting another run. Result storage can keep MLS busy after the arm task
has stopped. A confirmed stop does not open the gripper or run error recovery.

For example, from a laptop that can reach `nuc3`:

```python
from xmlrpc.client import ServerProxy, Transport

class StopTransport(Transport):
    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = 20
        return connection

with ServerProxy("http://10.180.68.124:8000", allow_none=True,
                 transport=StopTransport()) as mls:
    print("Stop acknowledged:", mls.stop_service())
    print("Learning still busy:", mls.is_busy())
```

Use the node's current reachable IP; `127.0.0.1` refers to the machine or
container running the client. From another Pod in the cluster, the runtime
Service is `http://mios-runtime.nuc3.svc.cluster.local:8000`.
`ml_service/example_learning.py` also supplies `stop_learning(host)`, which
requests both MLS/Core stops and checks that both return to idle.

Older images return `None` from `stop_service()` and only clear local loop
flags; an active Core task or reset movement can continue. To deploy the
fix, rebuild `mios_ml_service`, publish it with a new tag/digest, and update
the MLS image in `docker/k8s/kustomization.yaml`. Apply it using the
[supervised replacement procedure](#examples-and-supervised-replacement)
after the robot is stopped. Reusing a cached `latest` image with
`IfNotPresent` will not load the changed code. The API is application-level
cancellation; use the robot's stop controls when an immediate physical stop
is needed.

### Run learning from the host or a laptop

Keep Control, Core, ML, and MongoDB running, with the object grasped and the
effort controller configured and inactive. The object name in
`ml_service/example_learning.py` must exactly match teaching:

```python
example_learning("127.0.0.1", "janinetest1")
```

Before dispatch, the example checks Core and ML readiness and all three
saved objects: `janinetest1`,
`janinetest1_container_approach`, and `janinetest1_container`. These preflight
checks do not change gates, configure controllers, or activate them. A
missing or differently spelled name stops the run before arm control starts.

From the repository root, run supervised learning:

```bash
.venv/bin/python ml_service/example_learning.py
```

The current configuration keeps the requested 1,500-trial budget, one
candidate at a time. Check the nominal profile with the
[insertion diagnostic](../docs/insertion-diagnostic.md) before resuming
exploration. Core
activates and releases effort control for each control call. The controller
checks stationary joints at each activation, so skills must finish before
the next skill acquires control. Manual controller activation is not required. Keep an operator supervising the physical trials. Local
script edits take effect without rebuilding or copying files into the ML
container.

Motion settings near the top of `ml_service/example_learning.py` separate
initial travel, contact search, and the return after each trial:

| Stage | Speed | Acceleration |
| --- | --- | --- |
| Initial joint travel to approach | 0.10 rad/s | 0.20 rad/s² |
| Insertion's initial Cartesian approach (every candidate) | 0.02 m/s / 0.10 rad/s | 0.10 m/s² / 0.20 rad/s² |
| First candidate's contact search | 0.02 m/s | Factory seed (0.05 m/s²) |
| Extraction translation / rotation | 0.02 m/s / 0.10 rad/s | 0.10 m/s² / 0.20 rad/s² |
| Joint return, rescue, termination | 0.05 rad/s | 0.10 rad/s² |

`FIRST_CONTACT_SPEED` changes only the first candidate's contact speed.
The insertion's initial Cartesian approach speed and acceleration remain
fixed for every candidate. Later candidates can vary contact speed and
other learned parameters within the original learning ranges. The return
settings apply to every trial, including both extraction phases; joint
speed alone does not control extraction. These are trajectory settings;
actual speed also depends on tracking and Control effort limits. Active
learning controls the arm's pose and resists manual displacement. Diagnose
reported twist-limit failures before another physical trial.

The engine also saves each pending candidate before dispatch and retains
its context and received replies if completion or reset fails. This engine
change requires rebuilding and deploying the MLS image; copying the client
script alone does not enable it. See the diagnostic guide's
[candidate evidence workflow](../docs/insertion-diagnostic.md#7-review-the-revised-approach-and-preserve-an-interrupted-learning-candidate)
for the read-only export procedure.

The learning host argument must identify the deployment where both the Core
Portal (port 12000) and ML service (fixed port 8000 in this example) are
reachable. The laptop does not need Docker, ROS, or direct access to MongoDB; MongoDB can remain bound to the deployment host's
loopback interface.

Stop the Control, Core, and MLS stack:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml down
```

The separately managed MongoDB container is unaffected by this command.

## Container startup

The images carry their own default service commands:

| Image | Default command | Responsibility |
| --- | --- | --- |
| Control | `/usr/local/bin/start_control.sh` | Start Franka drivers and prepare controllers; report startup readiness. |
| Core | `/usr/local/bin/start_core.sh` | Start the Portal and scheduler; acquire/release effort control through ROS for each control call. |
| MLS | `python3 ./start_interface.py` | Serve learning requests using Core and MongoDB. |

Core's environment variables use the same defaults as Compose. Runtime
names and image commands do not depend on `docker exec` or a Docker socket.
Control exposes
`/usr/local/bin/check_control_ready.sh` for a startup/readiness probe; this
checks successful preparation and the launch process, not end-to-end robot
health. Core waits for fresh state/model/gripper feedback before startup.

Allow at least 30 seconds of termination grace for Core and 20 seconds for
Control; Compose sets these service limits. The Kubernetes deployment below
uses ordered termination and a shared 90-second Pod grace period.

## Kubernetes deployment

[`docker/k8s`](k8s/) supplies one `mios-runtime` Deployment in namespace
`nuc3`: one Pod, `replicas: 1`, and `strategy: Recreate`. Use Kubernetes
**1.33 or newer** on the commissioned Linux amd64 robot node. Control and
Core are native sidecars (`initContainers` with `restartPolicy: Always`);
startup probes gate Control → Core → MLS. Kubernetes stops the main MLS
container before Core and then Control, in reverse sidecar order.
See [Kubernetes sidecar lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/).
An individual container restart does not restart the other services; use
supervised replacement after a runtime failure, not automatic task replay.
These manifests have not been applied to or commissioned on a cluster here.

### Configure the node and images

Use the existing [image build instructions](#build-and-start-the-stack).
Before applying, review the following in `docker/k8s`:

- `runtime.yml` pins the Pod containing Control, Core, and MLS to `nuc3`
  using `kubernetes.io/hostname: nuc3`. The node must have that hostname label
  and satisfy the Linux/amd64 selectors. Keep the single-replica deployment.
- Edit the `mios-runtime-config` literals in `kustomization.yaml` for
  `ROBOT_IP`, `ROS_DOMAIN_ID`, service ports, CPU masks, Mongo settings, and
  task/gripper gates. Match port changes in `runtime.yml` and the clients;
  MLS uses `MIOS_ML_PORT` and the following port. Compose environment exports
  do not modify these manifests. Defaults enable teaching/learning services
  but do not start an example.
- Edit the `images` entries in `kustomization.yaml` to identify the exact
  Control, Core, and MLS images. Use `newName`/`newTag`, or an immutable
  `digest`; configure registry credentials if required. Both configuration
  and helper code from `runtime.py` use generated ConfigMaps with content
  hashes, so editing either and applying changes the Pod template.

Docker's image store is separate from the node's Kubernetes container
runtime. Push the images to a registry the node can pull, or import an
archive on that node. For the supplied local image names:

```bash
docker save -o mios-runtime-images.tar \
  mios-ros2-control:local mios-ros2-core:local mios-ml-service:local
sudo ctr -n k8s.io images import mios-runtime-images.tar
```

For k3s, use `sudo k3s ctr images import mios-runtime-images.tar` instead.
Run the import against the containerd instance used by kubelet; copying
images only into another Docker daemon does not make them available to Pods.
Use new tags/digests when replacing images to avoid reusing a cached `local`
tag.

MongoDB remains a separately managed service on the robot node, normally
`127.0.0.1:27017`; an existing host-accessible Docker Mongo container can
remain running. Core's Mongo host is hardcoded to localhost. Pointing MLS
at external Mongo alone is insufficient; external Mongo requires application
changes. To provide Mongo on `nuc3`, use the optional
[MongoDB manifests](#mongodb-on-nuc3) below. They are applied separately from
the main Kustomization so runtime updates do not modify an existing database.

Retain the [commissioned real-time host settings](#real-time-cpu-placement).
The Control image fixes its controller thread to CPU 6. The Kubernetes
configuration uses robot IP `192.168.3.100` and sets
`MIOS_CONTROL_WORKER_CPUS=0-5,7-13,15` and
`MIOS_NONRT_CPUS=0-5,7-13,15` for `nuc3`'s reported CPUs 0–15 and SMT
sibling pair 6,14. CPUs 16–19 from the Docker defaults are unavailable to
this Pod. Core/MLS use
the same non-RT mask through `sched_setaffinity`, which does not reserve
CPUs exclusively in Kubernetes.

These masks exclude CPUs 6 and 14. Before teaching, verify CPU 6's actual SMT
sibling with `cat /sys/devices/system/cpu/cpu6/topology/thread_siblings_list`;
CPU 7 was the sibling on the original Docker host. Keep kubelet,
ordinary OS work, and other workloads off the controller CPU and its sibling.
Changing the controller CPU requires updating the image's installed
controller YAML and the helper/config masks together.
`MIOS_CONTROL_RT_CPU=6` only validates availability; it does not change the
image's controller YAML. Avoid CPU Manager allocations that exclude the
controller or worker CPUs from this Pod's effective cgroup CPU set.

The host IRQ service is separate from the Pod configuration. The
`docker/k8s/nuc3-nic-irq.conf` systemd drop-in sets its
`ROBOT_IP=192.168.3.100`, `MIOS_CONTROL_CPU=6`, and
`MIOS_FRANKA_IRQ_PRIORITY=90`; the shipped base unit's IP belongs to the
original Docker host. Install this drop-in on `nuc3` as
`/etc/systemd/system/mios-franka-nic-irq.service.d/20-nuc3.conf` before
starting the service. It is a host file, not a Kubernetes resource, and
`kubectl apply -k` does not install it. Install the current
`tools/pin_franka_nic_irq.sh`, which discovers every MSI/MSI-X queue IRQ and
matches IRQ threads by number, including truncated names. The `igc` interface
on `nuc3` uses queue names such as `enp3s0-TxRx-2`; checking only the bare
`enp3s0` interrupt misses its data queues. The `e1000e` module settings above
do not apply to this driver. Stop the whole MIOS runtime and confirm its
Pod has terminated before applying NIC settings, which can interrupt the
robot link. Verify effective IRQ affinity and FIFO priority afterwards.

If Control logs `Requested CPUs [...], allowed [...]`, startup stopped
before launching ROS because the configured mask was reduced by the host
or its cgroup restrictions. The returned mask is not a complete inventory
of the node's CPUs. Correct both worker masks in `kustomization.yaml` to
use available CPUs and retain the strict check in `runtime.py`. Changing
only these masks needs no image rebuild: copy the updated configuration to
the deployment folder and run `kubectl apply -k .`. The generated ConfigMap
hash replaces the Pod. Core and MLS wait until Control's startup succeeds.

Control runs as non-privileged root with `SYS_NICE`, `SYS_RESOURCE`, and
`IPC_LOCK`; its helper raises `rtprio` to 99 and removes the memlock limit.
There is no CPU limit. The node's CRI runtime/cgroups must actually permit
these limits and real-time scheduling. Namespace Pod Security Admission uses
`enforce: privileged` to permit host namespaces and capabilities; this does
not set `privileged: true` on the containers. Check cluster admission and
node runtime policies before deployment. The existing
[readiness checker](#check-readiness-before-deployment) covers the Docker/
Compose host and images, not Kubernetes CRI or admission certification.

### MongoDB on nuc3

[`k8s/mongo.yml`](k8s/mongo.yml) runs `DaemonSet/mongo` in namespace `nuc3`,
pinned to node hostname `nuc3`. It matches the supplied `nuc2` deployment's
`mongo:7.0.14`, `/data/db` mount, CPU/memory requests (`1`, `1Gi`), limits
(`2`, `5Gi`), and liveness/readiness timing. A startup probe additionally
allows database recovery before liveness checks begin. The `machine-type`
label from `nuc2` is not required on the target node.

Mongo uses host networking and binds explicitly to `127.0.0.1:27017` for
Core/MLS on the same node. No Mongo Service is needed. This supplies local
database access without exposing an unauthenticated listener on the node's
LAN interfaces; the official image otherwise adds `--bind_ip_all` when no
binding is supplied. See the [Mongo image entrypoint](https://github.com/docker-library/mongo/blob/master/docker-entrypoint.sh).

An earlier cluster inventory already showed `nuc3/mongo-7dkst` running.
Check the existing workload and its claim before applying these files:

```bash
kubectl -n nuc3 get daemonset/mongo persistentvolumeclaim/mongo-data-dir -o yaml
kubectl -n nuc3 get pods -l name=mongo -o wide
kubectl -n nuc2 get pvc mongo-data-dir -o yaml
kubectl get storageclass
```

If the existing `nuc3` Mongo already serves MIOS, reuse it and skip deployment.
Keep its PVC and its current configuration, including any authentication or
remote clients. If replacing an existing DaemonSet, first stop active
teaching/learning, compare its configuration with this file, and update its
GitOps source if it is managed there. Do not start a second database on the
same host port or mount one database directory into two Mongo processes.

For a new database, [`k8s/mongo-pvc.yml`](k8s/mongo-pvc.yml) supplies a
**10Gi example**, using the cluster's default StorageClass. The provided Pod
description did not include the original claim's capacity or StorageClass;
match those from the `nuc2` PVC output before creating the new claim. If
there is no default class, set `storageClassName` to an available class.
Reuse an existing `nuc3/mongo-data-dir` claim without applying this template.
Claims are namespace-scoped; a new `nuc3` claim starts a separate database
and does not copy `nuc2`'s records. See [Kubernetes persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/).

From the repository root, after reviewing the storage settings:

```bash
kubectl apply -f docker/k8s/namespace.yml
# Only when nuc3/mongo-data-dir does not already exist:
kubectl apply -f docker/k8s/mongo-pvc.yml
kubectl apply -f docker/k8s/mongo.yml
kubectl -n nuc3 rollout status daemonset/mongo --timeout=10m
kubectl -n nuc3 exec daemonset/mongo -- mongosh --quiet --host 127.0.0.1 \
  --eval 'quit(db.adminCommand({ping: 1}).ok === 1 ? 0 : 1)'
kubectl -n nuc3 logs daemonset/mongo --tail=100
```

When the files are copied into your online deployment folder, use
`kubectl apply -f mongo-pvc.yml` (new claim only) and
`kubectl apply -f mongo.yml`. Applying the main `kustomization.yaml` does
not install Mongo. Keep the PVC when stopping or updating Mongo; deleting
it can also delete the stored data, depending on the StorageClass policy.

### Deploy and inspect

The Pod uses `hostNetwork` and `hostIPC` for the existing localhost and ROS
communication contracts, with `dnsPolicy: ClusterFirstWithHostNet` for
[cluster DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/).
The `mios-runtime` ClusterIP Service exposes Core TCP 12000/12001, Core UDP
12002, and MLS TCP 8000/8001. Host networking also exposes these listeners
on the node without a NodePort Service. All five `hostPort` declarations
live on the main MLS container so Kubernetes 1.33 reserves them during
scheduling; Core still serves its own ports in the shared network namespace.
Use a trusted network and host firewall rules: the Portal has no authentication.

Render and review locally before deploying:

```bash
kubectl kustomize docker/k8s
```

After stopping active teaching/learning and confirming Core is idle, stop
the old three-container stack, leaving MongoDB running. Then deploy:

```bash
docker compose -f docker/ros2/docker-compose.runtime.yml down
kubectl apply -k docker/k8s
kubectl -n nuc3 rollout status deployment/mios-runtime --timeout=10m
kubectl -n nuc3 get pods -o wide
kubectl -n nuc3 logs deployment/mios-runtime -c control
kubectl -n nuc3 logs deployment/mios-runtime -c core
kubectl -n nuc3 logs deployment/mios-runtime -c mls
```

When already in `docker/k8s`, use `kubectl apply -k .`. Using `-f ./`
submits `Kustomization` as an API resource and skips the generated ConfigMaps;
use `-k` to render them. No Kustomization CRD is needed.
Changing namespaces creates separate resources: before deployment, stop and
remove the previous `mios-runtime` workload in its actual namespace (an earlier
`-f ./` may have used your context's namespace), preserving that namespace
and its other resources and data.

Control holds `/var/lock/mios-fr3/fci.lock` through a hostPath volume to
exclude another cooperating Kubernetes FCI owner on the same node. The
Docker stack does not use this lock: it must be stopped separately. The
lock does not prevent another node or unrelated SDK process owning FCI.

Readiness checks are read-only: Control checks its preparation marker and
launch process. Core's Portal listener must belong to its container's PID 1;
MLS listeners on TCP 8000/8001 must belong to its supervised child, verified
by PID, start time, and parent PID. These ownership checks precede TCP
connections, preventing an old Docker listener from satisfying the new
service's readiness check. Busy services can remain ready; readiness is not
authorization for motion. To inspect Control and its configured controllers:

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- /usr/local/bin/check_control_ready.sh
kubectl -n nuc3 exec deployment/mios-runtime -c control -- bash --noprofile --norc -c '
  source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash &&
  ros2 control list_controllers -c /controller_manager
'
```

Check effective CPU affinity, cgroup CPU availability, RT limits, and NIC IRQ
placement on the running node as well as the manifest. Before teaching,
expect effort and joint-position controllers inactive and Core idle.

### Pending Pod: host ports already reserved

If `FailedScheduling` reports one node without free requested ports and six
nodes that do not match the selector, the selector is working: `nuc3` is the
eligible node, but another scheduled Pod reserves at least one of TCP
12000/12001/8000/8001 or UDP 12002. This scheduler check uses Pod port
reservations, so the conflicting application need not be listening yet.
See the [Kubernetes host-port scheduler check](https://github.com/kubernetes/kubernetes/blob/v1.33.0/pkg/scheduler/framework/plugins/nodeports/node_ports.go).

Find the owner across all namespaces, including old deployments left by
the namespace change or an earlier `kubectl apply -f ./`:

```bash
kubectl get pods -A --field-selector spec.nodeName=nuc3 \
  -o 'custom-columns=NAMESPACE:.metadata.namespace,POD:.metadata.name,STATUS:.status.phase,HOSTPORTS:.spec.containers[*].ports[*].hostPort,OWNER:.metadata.ownerReferences[0].name'
kubectl get deployments -A -l app.kubernetes.io/name=mios-runtime
```

Inspect the conflicting Pod with `kubectl -n NAMESPACE describe pod POD` to
confirm the port/protocol and owner. A ReplicaSet owner can be traced to
its Deployment with `kubectl -n NAMESPACE describe replicaset REPLICASET`.
An old MIOS Pod may be in `mios`, `default`, or your earlier context's namespace.

If the owner is a confirmed obsolete `mios-runtime` Deployment in another
namespace, stop its active teaching/learning and confirm Core is idle, then
scale down that Deployment. Replace the namespace below with the verified
old namespace; keep the new `nuc3` Deployment running:

```bash
OLD_NAMESPACE=replace-with-confirmed-old-namespace
kubectl -n "$OLD_NAMESPACE" scale deployment/mios-runtime --replicas=0
kubectl -n "$OLD_NAMESPACE" wait --for=delete pod \
  -l app.kubernetes.io/name=mios-runtime --timeout=180s
kubectl -n nuc3 rollout status deployment/mios-runtime --timeout=10m
```

The pending Pod retries automatically after the old Pod terminates. Deleting
only an old Pod lets its controller recreate it. Keep the `hostPort`
declarations and node selector; resolve the reservation with its owner if
it belongs to another application. Docker containers and ordinary host
processes can also cause bind failures after scheduling, but are not the
Pod reservations reported by this scheduler error.

### Examples and supervised replacement

Follow the existing [teaching](#teach-from-the-host-or-a-laptop) and
[learning](#run-learning-from-the-host-or-a-laptop) instructions. On a laptop,
use the robot node's reachable IP as the example's host argument, not
`127.0.0.1`. Localhost works on the node or through SSH forwarding of all
three client ports: 12000, 8000, and 8001. ROS and Mongo remain on the node.
Inspect and edit the script's entrypoint before running it:
`python/mios_examples.py` can execute gripper homing and is not a read-only
health check. Homing requires the operator to confirm the fingers are empty
and clear; do not run the current entrypoint merely to check connectivity.

For a restart or image/config replacement, stop active learning through its
normal stop path and confirm Core has released control before scaling down.
MLS's preStop verifies its own listener before requesting `stop_service`
with a five-second socket timeout; this is not proof that a learning task
finished. Its supervisor forwards SIGTERM/SIGINT to the child process group,
including optimizer children, and escalates to SIGKILL if the child has not
exited after ten seconds. Core then receives SIGTERM while Control is
available, and Control's wrapper forwards SIGINT to its launch process.
The shared Pod grace period remains 90 seconds.

```bash
kubectl -n nuc3 scale deployment/mios-runtime --replicas=0
kubectl -n nuc3 wait --for=delete pod -l app.kubernetes.io/name=mios-runtime --timeout=180s
kubectl -n nuc3 scale deployment/mios-runtime --replicas=1
kubectl -n nuc3 rollout status deployment/mios-runtime --timeout=10m
```

For changed images/config, render and review the changes, then replace the
scale-to-one command with `kubectl apply -k docker/k8s` after deletion completes.
Wait for the old Pod to terminate before replacement; do not force-delete,
use an HPA/multiple replicas, or fail over to another node. If shutdown or
the node fails, establish the previous robot owner's state before starting
another Pod. Startup ordering and probes do not provide physical recovery.
