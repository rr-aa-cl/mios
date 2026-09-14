# Three-repository split

This repository is being prepared for a split into three independently
versioned components.  Until the public contracts are released, the source
tree remains a monorepo and is the integration workspace.

## Ownership

| Future repository | Owns | Must not own |
| --- | --- | --- |
| `mios-core` | MIOS Core, memory, task engine, Portal, safety, `mios_msgs`, `mios_ros2_runtime`, and the Core image | Franka FCI ownership or a hardware launch process |
| `mios-control` | `mios_ros2_control`, Franka launch/configuration, NIC/RT tooling, the Franka patch, and the control image | MIOS Core implementation or learning logic |
| `mios-mls` | `ml_service`, learning definitions, optimization, and ML tests | ROS controller commands, libfranka, or FCI ownership |

`mios-control` is the only component permitted to own FCI.  `mios-core` sends
typed ROS task/command messages through the published runtime contract, and
`mios-mls` uses only Core's Portal/WebSocket and database APIs.

## Current-to-future mapping

| Current path | Future owner |
| --- | --- |
| `src/{core,interface,memory,task,skill,safety,libraries,portal,utils,ros2_core_runtime}` | `mios-core` |
| `include/`, `cmake/`, `CMakeLists.txt`, `conanfile.txt` | `mios-core` |
| `ros2_ws/src/mios_msgs` | `mios-core` public ROS contract |
| `ros2_ws/src/mios_ros2_runtime` | `mios-core` ROS adapter |
| `ros2_ws/src/mios_ros2_control` | `mios-control` |
| `docker/ros2/franka_combined_control.patch`, controller config, NIC IRQ service/script | `mios-control` |
| `docker/ros2/docker-compose.runtime.yml` | `mios-control` deployment manifest |
| `ml_service/`, `docker/ml_service/` | `mios-mls` |

The existing teaching client is transitional: `python/mios_examples.py` stays
with `mios-control` because it manages the local ROS controller lifecycle.

## Required published contracts

The current release manifest is [`contracts/core-contract.json`](../contracts/core-contract.json).
Before extracting repositories, `mios-core` must publish that contract and:

1. `mios_msgs` ROS interfaces.
2. `mios_ros2_runtime` headers and libraries.
3. The neutral C++ types currently exported from
   `src/utils/include/mios/control` and
   `src/core/include/mios/core/robot_backend.hpp`.
4. The Portal/WebSocket request and response schema used by `mios-mls`.

The versioned manifest also fixes the default ROS topic names and QoS intent
(depth one, best effort).  Deployments may override names through ROS
parameters, but an override is not a different contract version.

The compatibility policy is semantic versioning: a control or MLS release
pins an explicit Core contract version; breaking interface changes require a
new major version.

## Extraction order

1. Publish Core ROS and Portal contracts from this monorepo.
2. Make the control Docker build consume those published Core artifacts,
   rather than relative source paths.
3. Make MLS CI run against a tagged Core API contract.
4. Extract `mios-core`, then `mios-control`, then `mios-mls`, preserving Git
   history with `git filter-repo`.
5. Create a small integration/deployment repository only if a single place is
   needed to pin the three released image versions.

No physical robot behavior changes during phase 1.  The current two-image
Docker targets remain the integration test topology until the first published
Core contract is available.
