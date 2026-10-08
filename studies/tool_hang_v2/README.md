# Empty-closure handoff comparison

The [protocol](protocol.md) schedules four episodes on two starts. [Results](results.json)
retain every scheduled outcome, including incomplete episodes. The first pair is
exploratory because its baseline initial prompt could not be verified; only the
second pair has matched saved common instructions. See [the erratum](amendment_002_encrypted_input_erratum.json).

Run these commands from the repository root:

```sh
.venv/bin/python studies/tool_hang_v2/analyze.py
.venv/bin/python studies/tool_hang_v2/initial_match.py
.venv/bin/python studies/tool_hang_v2/replay.py --run runs/th_v2_s02_guard
.venv/bin/python studies/tool_hang_v2/native_diagnosis.py
.venv/bin/python studies/tool_hang_v2/interrupt_diagnosis.py
```

Change the replay run path to another completed episode. Replay needs no model
access. It reconstructs the original initialization and verifies actions, states,
public cameras/calibration, native scoring and processed sensor feedback. Use this
v2 replay command for these runs; the older generic replay path resets cached
observable sampling differently and is unsuitable for the strict camera check.

Each `runs/th_v2_*` folder retains configuration, policy-visible initial and
follow-up text, raw returned commands, executed actions, public observations,
sensor feedback, native usage records, tool/calculation logs, outcome and replay
verification. Short command reasons are public self-reports, compared with sensors
and execution in `causal_review.json`; private internal reasoning is not exported.
Private geometry files diagnose outcomes and never drive the policy or executor.

Original simulator processes disappeared during intentional root interruptions in
both second-start episodes. Their per-run recovery sources, checks and interruption
records preserve the original contexts and budgets. Recovered prefixes match all
retained original robot/object/scoring records and final images, but original full
hidden prefix state arrays were not retained. Final recovered trajectories can be
replayed exactly. Missing dispatch/delivery intervals remain null, not zero.

Episode videos are retained locally and ignored by Git; actions, public snapshots
and trajectories are retained for deterministic replay. To launch a new policy run,
use the frozen start/preparation commands in the protocol and follow the robot-policy
routing skill. Verification and analysis do not call Astra. Do not overwrite an
existing scheduled episode or silently replace an interrupted or failed run.
