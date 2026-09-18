# Diagnose an assigned learning agent

`Agent ... is still assigned to a trial worker; waiting.` means the engine has
reserved that agent for a worker. The older message was
`Agent ... not in self.free_agents`. Both describe local scheduling state.
An assigned worker may be executing the candidate, resetting the robot,
waiting for Core, or saving results. Physical insertion alignment is a separate
diagnostic.

The assigned-agent message is limited to once every **30 seconds per agent**.
It does not by itself establish a fault. The scheduler checks other agents and
yields while none is available.

## Read the existing evidence

Run these in code-server. They read logs and do not start a learning trial:

```bash
kubectl -n nuc3 logs deployment/mios-runtime -c mls --timestamps --tail=150
kubectl -n nuc3 logs deployment/mios-runtime -c core --timestamps --tail=150
```

Look for the last accepted task UUID and the corresponding completion or
cancellation. The engine logs `Core accepted task ... with UUID ...` followed
by `Waiting for Core task ...`. Core's logs distinguish a queued task from one
that actually began executing. Startup-only MLS logs contain no evidence of an
assigned trial worker.

The September 16 failure showed a robot reflex, followed by a reset UUID queued
on Core and a lost completion response. That sequence explains why a worker
was waiting; it does not demonstrate that the availability set lost an entry.

## Worker release and failure handling

- A worker returns its agent to the availability set in `finally`. The
  scheduler also waits for that thread to finish before reusing the agent.
- If a trial thread cannot start, the scheduler restores its reservation and
  queue accounting before stopping learning.
- Missing, malformed, or rejected task acknowledgements cancel learning and
  request a Core stop with its queue cleared and recovery disabled. An
  uncertain start is never treated as permission to start the task again.
- Fresh `TaskError`, `RealTimeError`, and `UserStopped` results cancel learning
  before reset or requeue. A valid unsuccessful candidate without those faults
  can still be evaluated normally.
- Reset/rescue preconditions apply to the whole instruction. A mismatched
  precondition skips that instruction. An unreadable or invalid state cancels
  learning. The insertion reset's state check rejects `Reflex` and
  `UserStopped` even when the grasped-object name matches.

An agent returning to `free_agents` is not confirmation that Core stopped. The
engine separately retains unresolved Core ownership. MLS remains busy after an
unacknowledged stop, and the stopped engine cannot dispatch new work. Use the
existing [MLS stop procedure](../docker/README.md#stop-learning-through-the-mls-api)
to resolve cancellation; do not force an active worker's agent into the free
set or advertise the service as idle before cleanup.

## Verify the server code

The MLS image copies `ml_service/` into `/mios_mls/`. Editing the client in
code-server does not update the running server. This check reads server files
without importing or executing the engine:

```bash
kubectl -n nuc3 exec -i deployment/mios-runtime -c mls -- python3 - <<'PY'
from pathlib import Path
p = Path('/mios_mls/engine/engine.py')
s = p.read_text()
print('Engine file:', p)
for label, marker in (
    ('30-second assigned-agent throttle', 'wait_log_time + 30.0'),
    ('Cancel unconfirmed start', 'Core did not confirm starting task'),
    ('Cancel unusable completion', 'Core did not confirm a usable completion'),
    ('Whole-instruction precondition check', 'def _instruction_preconditions_met'),
    ('Fresh variation errors', 'error in variation_result.errors'),
):
    print(label + ':', marker in s)
PY
```

These markers identify the files on disk. If code was replaced inside an
already-running container, the process can still hold its previously imported
module. Deploy a newly built MLS image with a distinct tag or digest using the
[supervised replacement procedure](../docker/README.md#examples-and-supervised-replacement).
The repository's default `IfNotPresent` policy can reuse a cached `latest`
image. A deployment update can replace the whole runtime Pod, including Core
and Control, so preserve existing recordings and finish active robot work
before replacement.

The worker and transport failure regressions run with mocked Core and MongoDB
calls. They validate scheduling and cancellation behavior without executing
physical trials; deployment and robot behavior require separate verification.
