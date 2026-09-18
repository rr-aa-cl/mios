# One supervised insertion diagnostic on nuc3

Use this procedure to investigate the first-candidate insertion fault. Clearing
the robot's reflex does not correct its cause. Keep the normal learning client
stopped throughout this procedure. The operator must supervise the arm and have
its physical stop available.

The diagnostic client saves the taught Approach context before changing robot
state, sends the joint approach once, then checks both its result and measured
arrival against that saved target. It sends the nominal insertion once only
when those checks pass. It saves the commands, target, and Core replies.
It does not start MLS, retry a task, extract the object, or perform rescue motion.
The arm/object therefore remains at the final position after the attempt.

The diagnostic explicitly uses a **15-second insertion skill budget**, matching
the repository's insertion default. This includes the internal approach,
calibration, contact search, and wiggle phases. It overrides a shorter value in
the local insertion JSON for this diagnostic only; the shared learning
configuration is not edited. The client prints the budget before execution and
in its local preview. Existing force, torque, velocity, and ROI guards remain
in effect.

The shared `configure_supervised_motion()` helper also lowers the insertion's
internal approach phase (`p0`) to **0.02 m/s and 0.10 rad/s**, with acceleration
**0.10 m/s² and 0.20 rad/s²**. Both the diagnostic and learning example use this
profile. It gives the planned motion margin below the 1 rad/s measured twist
guard; it does not guarantee actual tracking or prevent a contact reflex.
The default factory JSON and the learned force, stiffness and offset ranges
are unchanged. The learning example retains the requested 1,500-candidate
budget; this diagnostic still executes only one nominal candidate.

## 1. Prepare the client without connecting to the robot

Use the updated project checkout in code-server, including
`ml_service/diagnose_insertion.py`, `ml_service/example_learning.py`, and
`ml_service/utils/ws_client.py`. Run from `~/mios/ml_service` in the same Python
environment used for learning:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --output insertion-plan
```

Without `--run`, this checks the local WebSocket client API and writes the
nominal plan; it makes no service calls. Expect `Local transport API check
passed. Dry-run plan written: ...`. Review the saved setup and insertion
contexts. Every invocation requires a new output directory so an earlier trace
cannot be overwritten.

### Preview the centered XY search locally

The optional `--search-profile centered-xy` selects a diagnostic-only search
profile. Omitting the option selects `nominal`; the learning service continues
to use its configured search. If the other client dependencies above are already
current, update only `ml_service/diagnose_insertion.py` in code-server. No image
rebuild or runtime restart is needed.

From `~/mios/ml_service`, create this local preview in a fresh directory:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --search-profile centered-xy \
  --output insertion-plan-centered-xy-1
```

This command makes no Core or MLS calls. The profile sets the lateral search
frequencies to **0.30 Hz in X and 0.15 Hz in Y**, with both phases zero. It keeps
the nominal **1 N lateral amplitudes**, **2 N axial push**, rotational settings,
15-second total skill budget, setup-arrival checks, and existing guards.

The raw XY search force forms a 2:1 figure-eight repeating every approximately
**6.667 seconds**. Both lateral components start at zero and have zero mean
over a full cycle. Partial cycles can have a nonzero mean. This describes the
requested force pattern; it does not guarantee an EE trajectory or insertion
success.

Review these local artifacts:

| File | Contents |
| --- | --- |
| `plan.json` | Exact requests, selected `search_profile`, and `parameter_overrides` |
| `search-preview.json` | Search summary calculated from the planned `p2` request |
| `search-preview.csv` | Raw search samples at 10 ms intervals from 0 through 15 seconds after wiggle entry |

The sampled signal excludes impedance forces, the separate feed-forward push,
frame transformations, and controller limits. The 15-second skill budget also
covers approach, calibration, and contact search, so actual wiggle time is
shorter than the preview's full interval. Review the preview files before
planning any physical attempt with this profile.

### Preview the setup-arrival check locally

If `example_learning.py` and `utils/ws_client.py` were already updated as above,
copy only the new `ml_service/diagnose_insertion.py` into the code-server
checkout. This arrival check runs in the diagnostic client; deploying it needs
no Docker image rebuild or runtime restart.

From `~/mios/ml_service`, use a fresh output directory:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --output insertion-plan-arrival-check-1
```

The saved `plan.json` must contain:

```json
{
  "setup_arrival_tolerances": {
    "position_m": 0.005,
    "orientation_rad": 0.0175,
    "joint_rad": 0.0175
  }
}
```

This preview makes no Core or MLS calls. It verifies the local plan and client
API; it cannot download the Approach, measure arrival, or establish clearance.
The target snapshot and arrival result described below are saved during an
explicit physical invocation. This update does not call for another attempt
while the previous mismatch is being investigated.

### If the client reports an unexpected timeout argument

An error such as `stop_task() got an unexpected keyword argument 'timeout'`
means code-server has an older `utils/ws_client.py`. Its generic `call_method()`
may also lack the connection and close timeout options. Copy both the updated
`ml_service/diagnose_insertion.py` and the complete
`ml_service/utils/ws_client.py` into the code-server checkout. Updating only the
diagnostic script is insufficient. This client update does not require a Docker
rebuild or a runtime restart.

Keep the timeout options: they bound connection, response, and close waits.
The updated diagnostic checks all transport layers before any Core/MLS call
and identifies the incompatible module's loaded path if the update is missing.

If the traceback stops at `clear_queue(..., "before")` with that argument error,
the diagnostic has not sent setup or insertion. That failed wrapper call also
did not clear Core's queue; the old generic stop warning is not evidence that
this attempt moved the robot. Preserve the failed run's output directory.

After copying the files, validate locally using a fresh directory:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --output insertion-plan-2
```

Before a later physical attempt, start a fresh recording as described below.
If `insertion-trial-1` or `/tmp/insertion-diagnostic-1` was already created,
use `insertion-trial-2` and `/tmp/insertion-diagnostic-2` and update the copy
commands accordingly. Do not reuse the failed attempt's expired recording.

## 2. Start the ROS recording in a separate code-server terminal

The runtime must already be running and the arm stationary. The following
command only subscribes to existing topics. Its CPU mask excludes the control
CPU 6 and its SMT sibling 14 on this specific nuc3 host.

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    exec timeout --signal=INT 180s taskset -c 0-5,7-13,15 \
      ros2 bag record --disable-keyboard-controls \
        -o /tmp/insertion-diagnostic-1 \
        --topics /franka_robot_state_broadcaster/robot_state \
        /mios_robot_model_broadcaster/robot_model \
        /mios_effort_controller/mios_effort_command \
        /mios_effort_controller/mios_actuator_command
  '
```

Wait for the recorder to report subscriptions to all four topics. If the
command is unavailable, a topic cannot be discovered, the output path already
exists, or recording exits, resolve that before starting the physical attempt.
Use a new bag path for any later independently planned diagnostic.

The recorder stops after three minutes and flushes the bag. A `124` exit status
from `timeout` is expected at that deadline; still verify that the bag finalized.
Stopping the recorder does **not** stop the robot. Recordings use ROS delivery
and can miss samples; they are not a lossless hardware trace. Recording also
adds CPU/network/disk load, despite keeping recorder threads off the control
core. Do not enable high-volume Core per-cycle console logging for this test.

## 3. Run the single attempt while recording is active

From the first code-server terminal:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --output insertion-trial-1 --run
```

**This command can move the robot.** It requires the existing taught object,
approach, and container contexts. The object must already be grasped, as in
`example_learning.py`; the client does not operate the gripper. It verifies
Core/MLS readiness, asks Core to clear pending tasks without recovery, checks
readiness again, then executes setup once. Insertion follows only after the
setup result and measured arrival pass. It attempts a final
stop with queue clearing on success, error, timeout, or keyboard interrupt.

If a stage fails, leave learning stopped and save the evidence. If software
cannot confirm stopping or the arm moves unexpectedly, use the physical stop.
Do not clear a reflex while pending task cancellation is unconfirmed.

### If setup completes but the arrival check fails

A successful `MoveToPoseJoint` task result alone does not confirm that the arm
arrived at the taught Approach. Before any robot-state mutation, the updated
client downloads the actual setup Approach and writes `setup-target.json`.
After setup it requires a valid Core state with `Idle`, `IdleTask`, and inactive
control, seven finite joint measurements, and a valid finite column-major EE
pose. It compares that measured state with the cached target using all three
checks:

| Arrival comparison | Maximum difference |
| --- | --- |
| Euclidean EE position distance | 0.005 m (5 mm) |
| Full EE orientation angle | 0.0175 rad (about 1°) |
| Each measured joint versus its taught joint target | 0.0175 rad (about 1°) |

Joint differences are compared directly, without wrapping by multiples of
2π. Nonzero setup joint offsets are unsupported and fail preflight before
motion. These are diagnostic acceptance thresholds. Hole alignment and
insertion behavior still need separate evaluation after setup passes.

The check records `setup.arrival_check` in `events.jsonl`, with
`position_error_m`, `orientation_error_rad`, seven absolute `joint_errors_rad`,
`max_joint_error_rad`, the tolerances, and `passed`. Invalid measured state
records `passed: false`, null differences, and an error description. The client
prints `Diagnostic setup arrival failed` and reports that insertion was not
dispatched. Its final cleanup requests Core stop with queue clearing and
recovery disabled. Preserve that event, the raw taught context in
`setup-target.json`, and the setup/Core state replies together. The guard ends
the attempt; it does not retry setup, perform rescue, or fix tracking.

Use the joint and Cartesian comparisons together:

- If joints match but EE pose does not, check consistency between the saved
  Approach joint/pose pair and the active tool/frame definitions. That pattern
  alone does not identify which value is wrong.
- If joints miss their targets, investigate joint arrival, tracking, and any
  movement between setup completion and the saved state sample using the
  matching recording and Core/Control logs.

For the September 17 pasted state and separately supplied Approach, the
calculated differences were **21.689 mm and 2.454°**, above these thresholds.
The supplied joint targets also show a joint 4 difference of **0.044834 rad
(2.569°)**: target -2.015756 rad, measured -2.060591 rad. Every other joint
differs by less than 0.375°. This comparison identifies measured joint arrival
as an issue to investigate, beyond the Cartesian difference alone.
The older run did not capture its Approach at dispatch, so those figures are
a comparison against the supplied reference, not proof of that run's exact
target or the cause of its mismatch. The new snapshot records the exact
reference used by the arrival check for future diagnostic records.

### If Core returns `success: False`

A result containing `skill_results.insertion` and `success: False` means the
client received an unsuccessful insertion result from Core. Updating
`ws_client.py` fixes the transport API; the skill's stopping condition must
now be diagnosed from its recorded result and Core logs. This result requires
no transport update or repeat motion to inspect.

The diagnostic exits with a nonzero status after attempting its final stop.
The updated client prints `Diagnostic trial unsuccessful` for a valid failed
result without a task exception or external stop. Older copies print a
`RuntimeError: Task failed or returned an ambiguous result` traceback for the
same result. Both preserve the full response in `events.jsonl` and end the
attempt without reset, rescue, or retry. Check the `finally.stop_task` and
`after.state` events to assess cleanup; the failure message itself is not an
idle-state confirmation.

An empty task `error` list does not rule out a skill guard, such as the time,
ROI, or velocity limit. Core logs the guard that fired. `cost.time` is elapsed
time at the last cost update. A value of exactly `5.0` suggests checking the
skill time limit, but does not establish which guard ended the attempt.

These time settings have separate purposes:

| Setting | Purpose |
| --- | --- |
| `skills.insertion.skill.time_max` in the saved plan | Skill execution limit sent to Core |
| `TimeMetric("insertion", {"time": 15})` | Learning score normalization |
| `RPC_LIMITS["timeout"] = 5` | Response wait for short Core requests |
| `TASK_WAIT_SECONDS = 50` | Client wait for an individual task result |

Inspect the existing attempt from code-server; change the directory below to
the one that produced the failure. These commands do not initiate robot motion:

```bash
python - <<'PY'
import json
from pathlib import Path

p = Path('insertion-trial-2')
plan = json.loads((p / 'plan.json').read_text())
for task in plan['tasks']:
    if task['stage'] == 'insertion':
        skill = task['request']['parameters']['skills']['insertion']['skill']
        print('Sent insertion time_max:', skill.get('time_max'))
for line in (p / 'events.jsonl').read_text().splitlines():
    event = json.loads(line)
    if event['operation'] in ('insertion.start_task', 'insertion.wait_for_task',
                              'finally.stop_task', 'after.state') and event['kind'] != 'request':
        print(json.dumps(event))
PY

kubectl -n nuc3 logs deployment/mios-runtime -c core \
  --since=30m --timestamps --tail=200
```

Match Core's log time and task UUID to the saved insertion event. If the
attempt is older than the displayed log window, retrieve the corresponding
time range or inspect the logs saved in the next section. Preserve the bag
and investigate the recorded condition before changing limits or retrying.

If the sent plan shows `time_max: 5` and Core reports `maximum time limit of
5.000000 s`, the five-second skill deadline caused that failure. A transition
to wiggle after about 4.5 seconds leaves only half a second for that phase.
Use the updated diagnostic's explicit 15-second budget for a later single
supervised, recorded attempt, first confirming it in a new dry-run plan.
More time does not guarantee insertion success or establish that an earlier
torque/velocity fault is resolved.

## 4. Preserve the evidence before restarting or removing the Pod

After the recorder exits, verify that the bag contains messages and copy it to
code-server. These commands do not replay its commands to the robot.

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    ros2 bag info /tmp/insertion-diagnostic-1
  '

diagnostic_pod=$(kubectl -n nuc3 get pod \
  -l app.kubernetes.io/name=mios-runtime \
  -o jsonpath='{.items[0].metadata.name}')

kubectl -n nuc3 cp -c control \
  "$diagnostic_pod:/tmp/insertion-diagnostic-1" ./insertion-trace-1

kubectl -n nuc3 logs "$diagnostic_pod" -c core \
  --since=15m --timestamps > insertion-core.log

kubectl -n nuc3 logs "$diagnostic_pod" -c control \
  --since=15m --timestamps > insertion-control.log
```

Keep `insertion-trial-1/`, `insertion-trace-1/`, and both log files. The bag's
robot-state messages contain measured joint effort, desired joint effort as
reported by Franka, velocity, mode, and current/last-motion errors. The two MIOS
command topics show incoming torque or impedance requests; impedance requests
are evaluated into torque inside Control. The model topic supports offline
interpretation of their frames and dynamics. Franka's desired torque includes
the effect of downstream command processing; it is not a direct measurement
of the ROS controller's pre-filter output.

The existing effort diagnostic publisher is disabled in the default ordinary
controller. This procedure does not enable it or reconfigure controllers. Its
absence is not a recording failure; it is not among the four required topics.

For CLI options and recording behavior, see the
[ROS 2 Jazzy rosbag2 documentation](https://github.com/ros2/rosbag2/blob/jazzy/README.md).

### If `ros2 bag info` reports missing metadata

The recorder's timeout status `124` is expected after 180 seconds. Check the
existing files before repeating a physical attempt. Use the exact Pod and
`control` container that recorded the bag; its `/tmp` files are not persistent
across container or Pod replacement. Substitute the actual bag directory in
these examples:

```bash
kubectl -n nuc3 exec "$diagnostic_pod" -c control -- \
  ls -lh /tmp/insertion-diagnostic-1
```

If an MCAP file exists, inspect it directly even when `metadata.yaml` is absent:

```bash
kubectl -n nuc3 exec "$diagnostic_pod" -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    ros2 bag info -s mcap \
      /tmp/insertion-diagnostic-1/insertion-diagnostic-1_0.mcap
  '
```

Use the actual filename from the listing if it differs. If the data is
readable and only the directory metadata is missing, reconstruct it:

```bash
kubectl -n nuc3 exec "$diagnostic_pod" -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    ros2 bag reindex -s mcap /tmp/insertion-diagnostic-1 &&
    ros2 bag info /tmp/insertion-diagnostic-1
  '
```

Reindexing writes metadata from existing storage files; it cannot reconstruct
an unrecorded trial. See the [Jazzy reindex implementation](https://github.com/ros2/rosbag2/blob/jazzy/ros2bag/ros2bag/verb/reindex.py).
If the directory or data file is absent, first locate the recording in the
original container or an existing copy. Preserve any reader error if the file
exists but cannot be opened.

Compare the bag's start/end times with the setup and insertion timestamps in
the diagnostic's `events.jsonl`. The physical trial must run while the recorder
is active in the other terminal. If it started after the recorder stopped,
the earlier bag does not contain that trial, even if metadata recovery succeeds.

## 5. Summarize an existing recording without another trial

`tools/analyze_insertion_bag.py` reads an MCAP bag directly. It creates no ROS
node and does not replay, publish, or send commands to Core or MLS. Run it with
the message packages from the Control image that recorded the bag. It filters
the selected time window and excludes the large robot-model topic.

The following example is for the **2026-09-16 10:26 trial of samuelnew2** and
the taught Container pose supplied for that trial. From `~/mios/ml_service`
in code-server, first copy the new `tools/analyze_insertion_bag.py` into the
matching checkout. Then run:

```bash
kubectl -n nuc3 exec -i deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    exec taskset -c 0-5,7-13,15 /usr/bin/python3 - \
      /tmp/insertion-diagnostic-1 \
      --start 2026-09-16T10:26:34Z --end 2026-09-16T10:26:54Z \
      --target-xyz 0.6263790726661682 0.09641637653112411 0.6374954581260681 \
      --axis 0.9998961088589333 -0.010074761474690302 0.010308766657195712 \
      --effort-limits 2 2 2 2 2 2 2 --effort-rate-limit 10
  ' < ../tools/analyze_insertion_bag.py > insertion-bag-force-summary.json
```

This passes the local script through standard input and leaves the recording
in place. Share `insertion-bag-force-summary.json` for analysis. If the command fails,
share its terminal error; a redirected output file alone does not establish
that analysis completed. No image rebuild or runtime restart is needed.

For other trials, use their recorded UTC times and taught Container pose.
`--target-xyz` is `O_T_OB[12:15]`; `--axis` is `O_T_OB[8:11]`, the Container's
positive Z axis expressed in the robot base frame, for the flat column-major
arrays returned by Core. The default success tolerances are 2 mm in depth and
3 mm laterally; match `--depth-tolerance-mm` and `--lateral-tolerance-mm` to
the saved plan if it differs. The goal and axis must be from the teaching
used by that trial, not a later retaught pose.

The report provides first, last and greatest-depth poses; one-second depth
and lateral-error ranges; samples satisfying both success conditions; robot
modes/errors; and requested versus Franka-reported desired joint torques.
Negative depth error means the EE is short of the taught Container depth.

The example window includes setup and controller release. Interpret it using
the Core phase times: insertion starts about 10:26:36.472, contact starts
10:26:36.912, wiggle starts 10:26:41.459, and stopping starts 10:26:51.479 UTC.
The last pose after release may differ from the last pose during insertion.
The timestamps used for filtering are bag receive timestamps; source stamps
are reported separately and may differ across hosts.

An empty `mios_actuator_command` topic is compatible with this trial's raw
`mios_effort_command` path. Command counts alone do not establish delivery to
the controller. Recorded gaps include recording effects and intentional
pauses between tasks. A command's `user_stopped` flag can also be set by Core's
normal stop/completion path; it does not by itself prove a physical user stop.
Requested-torque and Franka desired-torque maxima can occur at different
times, so their difference alone does not prove torque saturation.

The updated report also includes `force_and_limits` for the whole window and
each second. It projects the recorded base-frame external force onto the
Container insertion axis and reports the sideways force magnitude. It also
reports stiffness-frame force Z and the angle between the EE and Container
Z axes. These are estimates from the recorded Franka state; no calibration
bias has been subtracted. Axis alignment is not a full orientation-error
measurement and does not assess rotation about that axis.

The `--effort-limits` and `--effort-rate-limit` arguments are **offline
comparison values only**. They do not change any controller setting. The
example uses the 2 Nm / 10 Nm/s values read back from nuc3. Comparisons describe
the recorded trial only if those settings were unchanged since it.

The report counts requests above the torque bounds, MOVE-state samples whose
Franka desired torque is at those bounds, and requested torque changes faster
than the rate reference. It separately measures slew before and after applying
the reference amplitude bounds mathematically. At 1 kHz, 10 Nm/s corresponds
to 0.01 Nm per update, so the rate limiter can affect requests that stay below
2 Nm. Requested slew uses consecutive command source timestamps separated by
at most 10 ms; stop markers reset that calculation. These are sampled command
demand statistics, not a reconstruction of controller callback timing or its
actual output. They cannot independently prove how much motion a limit prevented.

To record the current configured effort limits alongside the report, use
this read-only query (values describe the trial only if unchanged since it):

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    ros2 param get /mios_effort_controller effort_limits &&
    ros2 param get /mios_effort_controller effort_rate_limit
  '
```

## 6. Re-teach only the approach, then record a new diagnostic

Use this procedure after comparing the manually seated pose with
`samuelnew2_container` on nuc3. The September 17 seated check found a 0.216 mm
lateral offset, a -0.113 mm axial offset, and a 0.959 degree orientation
difference. This supports checking the approach alignment next; it does not
establish that the saved orientation is exact for the physical fit.
Keep learning stopped. Begin with
the part held in the same grasp and manually seated, and supervise all guiding
and diagnostic motion. Keep the physical stop accessible.

Use the current `python/mios_examples.py` in code-server: its `handguiding()`
helper waits for control before prompting and for Idle after stopping. Import
the helper as shown below. Running that file directly invokes its separate
gripper example.

### A. Withdraw manually along the hole axis

In code-server terminal A, with the normal learning environment activated:

```bash
cd ~/mios/ml_service
python -c '
import sys
from example_learning import check_learning_services
check_learning_services("mios-runtime.nuc3")
sys.path.append("../python")
from mios_examples import handguiding
handguiding("mios-runtime.nuc3", "Withdraw the held part straight along the hole axis, preserving its orientation. Press Enter when fully clear and stationary: ")
'
```

Once the prompt appears, use your established hand-guiding technique to move
the part straight out of the hole. Preserve the grasp and orientation. The
direction is along the hole axis; for this teaching it is approximately robot
base **negative X**, not vertical. Judge clearance from the actual part and
fixture rather than commanding a guessed distance. Press Enter in terminal A
when the part is fully clear and the arm is stationary. Wait for the command
to return successfully before saving.

This uses `python -c` so Enter comes from the terminal. A Python heredoc would
consume standard input and cannot provide this interactive confirmation.

#### If freehand withdrawal drifts sideways or rotates

Use the read-only display below in a second terminal while using the same
handguiding procedure in terminal A. Copy the current
`ml_service/watch_insertion_alignment.py` to code-server first. It uses the
existing diagnostic client dependencies; no image rebuild is needed.

Use a `seated-reference-*.json` captured with the **current grasp**, after the
part seated freely and handguiding returned to Idle. Keep that file as the
reference. A new grasp, a moved fixture, or an edited Container requires a new
comparison before reusing it.

```bash
cd ~/mios/ml_service
python watch_insertion_alignment.py --robot mios-runtime.nuc3 \
  --reference seated-reference-20260917T075503288481Z.json
```

The display runs for 60 seconds and calls only `get_state`. It does not start
handguiding, move the arm, teach objects, or change stiffness or limits.
It reports:

- **X/Y and lateral:** drift from the line through the actual seated position,
  parallel to the saved Container Z axis, in millimetres.
- **Z:** position along that line; negative means withdrawn.
- **Rotation:** change from the actual seated orientation, in degrees.
- **Rot correction [Rx, Ry, Rz]:** signed rotation vector pointing toward the
  seated orientation, expressed about the fixed Container axes in degrees.
  Its length equals the total rotation difference. Positive signs follow the
  right-hand rule. These are components of one axis-angle rotation, not three
  sequential Euler rotations, robot base angles, or joint commands. At exactly
  180 degrees either axis sign describes the same rotation.

The reference for this display differs from section B: preserving the seated
alignment gives X/Y and rotation near **zero**, even if the seated pose itself
differs slightly from the saved Container. These are measured reference
differences, not a pass/fail decision or a measurement of hole clearance.
The axes are Container axes, not robot base axes.

The signed rotation components help identify the remaining orientation
difference when the total angle alone gives insufficient feedback. For example,
`rot correction [0.000, 0.000, -3.000] deg` indicates a rotation back toward the
seated orientation about negative Container Z. This is an orientation
comparison, not a request to turn any individual robot joint by three degrees.
The display cannot determine fixture clearance or prove a hand-guided
adjustment is unobstructed.

Use the feedback to notice drift during withdrawal, preserving the grasp and
seated orientation. Make any alignment adjustments while the part is fully
clear of the fixture. If the part is already fully clear and the grasp and
fixture are unchanged, use the existing handguiding helper at that clear pose
to adjust alignment against the saved reference; there is no need to repeat
seating merely to start the display.
Finish handguiding in terminal A, then check the display
again after the arm is stationary and reports Idle, before saving in section B.
Stopping the display with Ctrl-C or reaching its duration limit **does not stop
handguiding**. Restart the display if more time is needed.

#### If position drifts while you adjust the angle

The optional `handguiding(..., mode=...)` argument separates the two manual
adjustments. Copy the updated `python/mios_examples.py` to code-server first.
These modes use the existing Core `HandGuiding` skill; they need no image
rebuild when running the matching Core implementation.

| Mode | Manual adjustment | Spring resistance |
| --- | --- | --- |
| `free` (default) | Position and orientation | Neither |
| `rotate` | Orientation | Translation away from the starting position |
| `translate` | Position | Rotation away from the starting orientation |

**Each mode captures the current measured pose when control starts.** Starting
`rotate` at a sideways offset preserves that offset while you adjust the angle.
Starting `translate` preserves the orientation you currently have. Neither mode
automatically aligns to the seated reference. Translation is free in all three
directions in `translate` mode; it is not restricted to the hole axis.
The held position is the reported end-effector position. Turning it can still
sweep the held object's tip sideways.

These are springs, not rigid locks. Core requests 1500 N/m stiffness for held
translation axes or 150 Nm/rad for held rotation axes, subject to its limits.
The existing 2 Nm joint effort caps can allow drift. The helper does not raise
those caps. The mode selection and cleanup have offline tests; physical holding
performance still needs a short supervised check in clear space.

1. Finish the previous handguiding command with **Enter in terminal A** and
   wait for it to return to Idle. Keep learning stopped and the object securely
   held. Start the following checks only with the part fully clear of the
   fixture, including room for its tip to sweep as you turn it.
2. Run the alignment watcher above in terminal B. In terminal A, start
   `rotate` mode with the command below. Once prompted, make a small manual
   angular adjustment while watching X/Y/Z and rotation. Press Enter to stop
   after the short check. If position drifts substantially or the behavior is
   unexpected, stop and review it before continuing; do not push harder against
   the constraint.

```bash
cd ~/mios/ml_service
python -c '
import sys
from example_learning import check_learning_services
check_learning_services("mios-runtime.nuc3")
sys.path.insert(0, "../python")
from mios_examples import handguiding
handguiding("mios-runtime.nuc3", "In clear space, gently adjust orientation while watching alignment. Press Enter to stop: ", mode="rotate")
'
```

3. If the first check holds position adequately, use `rotate` mode to bring the
   orientation closer to the seated reference while clear of the fixture.
   Finish with Enter and check the stationary Idle readings. There is no need
   to force the displayed angle to exactly zero.
4. Then use `translate` mode below to adjust X/Y while resisting rotation.
   Keep the part withdrawn and judge fixture clearance physically; the watcher
   shows the end-effector reference position, not the part's swept volume.
   First check the orientation hold with a small movement. Stop if it yields
   substantially. Finish with Enter and review the Idle readings before saving
   any approach pose in section B.

```bash
cd ~/mios/ml_service
python -c '
import sys
from example_learning import check_learning_services
check_learning_services("mios-runtime.nuc3")
sys.path.insert(0, "../python")
from mios_examples import handguiding
handguiding("mios-runtime.nuc3", "In clear space, adjust position while watching alignment. Keep the part withdrawn. Press Enter to stop: ", mode="translate")
'
```

Both commands wait for control before prompting and for Idle after stopping.
They save no taught poses. The watcher remains a separate read-only display;
stopping it does not stop either guiding mode.

### B. Back up the teaching and save only the approach

Run this in terminal A while the arm stays at that withdrawn pose. This
changes the saved approach; it sends no motion or gripper commands. Core saves
both its measured Cartesian pose and joint configuration.

```bash
python - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from example_learning import check_learning_services
from utils.ws_client import call_method

robot = "mios-runtime.nuc3"
approach = "samuelnew2_container_approach"
container = "samuelnew2_container"

def rpc(method, payload):
    response = call_method(robot, 12000, method, payload,
                           timeout=5, open_timeout=5, close_timeout=0.2)
    result = response.get("result") if isinstance(response, dict) else None
    if not isinstance(result, dict) or result.get("result") is not True:
        raise RuntimeError(response)
    return result

def download(name):
    context = rpc("download_object_context", {"object": name}).get("context")
    if not isinstance(context, dict) or context.get("name") != name:
        raise RuntimeError(f"Invalid taught context: {name}")
    return context

check_learning_services(robot)
old = {name: download(name) for name in (approach, container)}
folder = Path("approach-teaching-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
folder.mkdir(exist_ok=False)
(folder / "before.json").write_text(json.dumps(old, indent=2) + "\n")
print("Backup:", folder, flush=True)

rpc("teach_object", {"object": approach})
new = {name: download(name) for name in (approach, container)}
(folder / "after.json").write_text(json.dumps(new, indent=2) + "\n")
if new[container] != old[container]:
    raise RuntimeError("Container changed during teaching; review the saved contexts before testing.")

a, c = new[approach]["O_T_OB"], new[container]["O_T_OB"]
offset = [1000 * sum(c[4*i+j] * (a[12+j] - c[12+j]) for j in range(3))
          for i in range(3)]
trace = sum(a[4*i+j] * c[4*i+j] for i in range(3) for j in range(3))
angle = math.degrees(math.acos(max(-1, min(1, (trace-1)/2))))
print("Saved approach with Cartesian pose and joint configuration.")
print("Approach offset in container axes [mm]:", offset)
print("Orientation difference [degrees]:", angle)
check_learning_services(robot)
PY
```

Review those values before testing. The third offset should be negative
(withdrawn from the seated target). The first two offsets should be close to
zero, and orientation should remain close to the seated orientation. The
manual seated pose in the September 17 check already differed from Container
by about 0.959 degrees, so preserving it does not imply a zero angular
difference. That angle can still matter for a tight fit, and the insertion
skill continues to target the saved Container orientation.
If the values indicate substantial sideways drift or rotation, review the
withdrawal before proceeding. An approximately zero depth offset means the
approach was saved at the seated position, which is not the intended approach.

### C. Preview a new trial locally

The following steps use the shared name `aligned-1`. If any of their output
paths already exist, choose another suffix and change it consistently in
both terminals. The preview and physical trial use separate directories.
Keep `centered-xy`, as in the preceding trial, to compare the approach change
without also changing the search profile.

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --search-profile centered-xy \
  --output insertion-plan-aligned-1
```

Expect the local API check to pass and the insertion budget to be 15 seconds.
The preview writes the request plan; it does not validate the physical poses.

### D. Start a fresh recording in terminal B

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    exec timeout --signal=INT 180s taskset -c 0-5,7-13,15 \
      ros2 bag record --disable-keyboard-controls \
        -o /tmp/insertion-diagnostic-aligned-1 \
        --topics /franka_robot_state_broadcaster/robot_state \
        /mios_robot_model_broadcaster/robot_model \
        /mios_effort_controller/mios_effort_command \
        /mios_effort_controller/mios_actuator_command
  '
```

Wait for subscriptions to all four topics, then proceed while this recorder
is still running. Its three-minute timeout finalizes the recording; status
124 at that deadline is expected. Stopping the recorder does not stop the arm.

### E. Run one supervised attempt in terminal A

**This command moves the robot.** Keep people clear of the motion and run it
once while recording is active:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --search-profile centered-xy \
  --output insertion-trial-aligned-1 --run
```

Let the diagnostic finish and perform its cleanup. It leaves the part at its
final pose. Keep learning stopped while reviewing the result. If a reflex or
an unconfirmed stop occurs, use the established stop procedure rather than
starting another attempt.

### F. Read the new result and preserve the recording

Run the following even if the diagnostic exits unsuccessfully:

```bash
python - <<'PY'
import json
from pathlib import Path
path = Path("insertion-trial-aligned-1/events.jsonl")
for line in path.read_text().splitlines():
    event = json.loads(line)
    if event.get("operation") in ("insertion.start_task", "insertion.wait_for_task",
                                   "finally.stop_task", "after.state") and event.get("kind") != "request":
        print(json.dumps(event))
PY
```

After terminal B exits, check and copy the new bag and logs:

```bash
kubectl -n nuc3 exec deployment/mios-runtime -c control -- \
  bash --noprofile --norc -c '
    source /opt/ros/jazzy/setup.bash &&
    source /ws/install/setup.bash &&
    ros2 bag info /tmp/insertion-diagnostic-aligned-1
  '

diagnostic_pod=$(kubectl -n nuc3 get pod \
  -l app.kubernetes.io/name=mios-runtime \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n nuc3 cp -c control \
  "$diagnostic_pod:/tmp/insertion-diagnostic-aligned-1" ./insertion-trace-aligned-1
kubectl -n nuc3 logs "$diagnostic_pod" -c core \
  --since=15m --timestamps > insertion-core-aligned-1.log
kubectl -n nuc3 logs "$diagnostic_pod" -c control \
  --since=15m --timestamps > insertion-control-aligned-1.log
```

Use the UTC timestamps from this trial's events for subsequent bag analysis.
The example 10:26 window in section 5 refers to the older failed trial. Use
the new bag and the saved `after.json` Container context when selecting this
attempt's analysis arguments.

## 7. Review the revised approach and preserve an interrupted learning candidate

### Preview the revised profile without moving the robot

Update the code-server copies of `ml_service/example_learning.py`,
`ml_service/diagnose_insertion.py`, and `ml_service/utils/ws_client.py` together.
Keep your learning entry point addressed to `mios-runtime.nuc3` and
`samuelnew2`; the repository example's entry point uses demonstration defaults.
The learning budget is 1,500 and batch width is one.

From `~/mios/ml_service`, create a new local preview:

```bash
python diagnose_insertion.py --robot mios-runtime.nuc3 \
  --insertable samuelnew2 --output insertion-plan-slow-approach-1
```

Expect:

```text
Insertion skill time limit: 15 s (includes approach, calibration, and search).
Insertion approach: 0.02 m/s, 0.1 rad/s; acceleration 0.1 m/s^2, 0.2 rad/s^2.
```

Review `plan.json` before a later supervised diagnostic. This preview makes no
Core or MLS calls. For that later diagnostic, use the recording and one-attempt
procedure in sections 2–4 with fresh, matching names throughout:

| Artifact | New name |
| --- | --- |
| Diagnostic output | `insertion-trial-slow-approach-1` |
| Bag in Control | `/tmp/insertion-diagnostic-slow-approach-1` |
| Copied bag | `insertion-trace-slow-approach-1` |
| Saved logs | `insertion-core-slow-approach-1.log`, `insertion-control-slow-approach-1.log` |

Keep learning stopped while assessing this single candidate. A nominal result
does not validate the full learning domain: later candidates still vary pose,
stiffness, speed and pushing force within the factory bounds.

### Compare the torque signals from that attempt

The existing four-topic recorder already captures the signals needed for this
comparison. Keep the confirmed 2 N·m / 10 N·m/s controller limits unchanged.
When using section 5's analyzer, substitute the **new bag and this attempt's UTC
times and Container pose**. The old 10:26 example window describes another run.

| Recorded signal | Meaning |
| --- | --- |
| `MiosEffortCommand.effort` | Core's torque request before the controller's outer limits |
| `FrankaRobotState.desired_joint_state.effort` | Franka's reported desired torque after downstream command processing, without gravity |
| `FrankaRobotState.measured_joint_state.effort` | Measured joint torque; this is not bounded by the 2 N·m command cap |

For the raw-effort command path used here, compare these report fields under
`force_and_limits` for each phase's time interval:

- `nonstop_requested_effort.above_limit_fraction`
- `move_franka_desired_effort.at_or_above_limit_fraction`
- `raw_requested_slew.above_rate_limit_fraction`
- `amplitude_clipped_requested_slew.above_rate_limit_fraction`

Requests above 2 N·m alongside Franka desired torque near 2 N·m support amplitude
limiting. Requested slew above 10 N·m/s identifies demand that the rate limiter
may attenuate. Separate maxima, or the configured limits alone, do not establish
clipping at a particular instant. The sampled statistics do not reconstruct
controller receipt/update timing or prove that limiting caused a reflex.
No additional diagnostic publisher or controller reconfiguration is needed.

### Preserve the candidate if a later learning reset fails

The updated MLS engine stores the exact insertion request in
`ml_results.insertion.pending_trials` **before dispatch**. It keeps the pending
record if dispatch, waiting, or reset is interrupted. A saved request establishes
what the client attempted; it does not establish that Core received or executed
it. After normal trial completion, the compact trial result replaces the pending
record. Thus a 1,500-trial run does not retain 1,500 full request contexts.
For a trial with result logging explicitly disabled, the transient request is
still preserved on interruption and removed after normal completion without
writing a compact result. A failed or unacknowledged audit write prevents a
new insertion dispatch; the database operation has a five-second deadline.

This feature requires rebuilding the **MLS image** and deploying its new
tag/digest; updating the code-server client alone does not update MLS. Follow
the [supervised image replacement instructions](../docker/README.md#examples-and-supervised-replacement)
after preserving current logs and stopping the run. It cannot recover the
missing candidate from the earlier interrupted experiment.

To export a new interrupted experiment without moving the robot, take its Mongo
experiment ID from the MLS log and replace the placeholder below. Use the
`(mios)` environment in code-server:

```bash
python - <<'PY'
from pathlib import Path
from bson import ObjectId, json_util
from pymongo import MongoClient

experiment_id = "PASTE_EXPERIMENT_ID_FROM_MLS_LOG"
with MongoClient("mios-runtime.nuc3", 27017,
                 serverSelectionTimeoutMS=5000,
                 connectTimeoutMS=5000, socketTimeoutMS=5000) as client:
    document = client.ml_results.insertion.find_one(
        {"_id": ObjectId(experiment_id)},
        {"meta": 1, "pending_trials": 1, "final_results": 1})
if document is None:
    raise SystemExit("Experiment not found; check the ID and database host.")
output = Path(f"learning-evidence-{experiment_id}.json")
with output.open("x") as stream:
    stream.write(json_util.dumps(document, indent=2) + "\n")
print(f"Saved {output}; pending trial IDs:", list(document.get("pending_trials", {})))
PY
```

Keep this export together with the matching Core/Control/MLS logs and bag.
Pending task contexts name taught objects; preserve the teaching used by the
run as well if those objects may subsequently be retaught.
