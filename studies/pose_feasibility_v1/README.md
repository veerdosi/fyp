# Pose-feasibility query: two-start paired study

This is a computational planning aid, not a new stop rule. Astra medium receives
the same public robot/sensor data and logged calculation access in both conditions.
The query condition additionally has an optional robot-only bounded IK command.
It neither moves the robot nor selects a target/recovery. Both conditions share
ordinary waypoint execution and the existing explicitly armed empty-closure behavior.

The [prospective mechanism protocol](../mechanism_selection/mechanism_protocol.json)
and [implemented freeze](protocol.json) specify two new matched starts / four episodes.
Run the declared order. Do not replace failures, add another start by default, or
report faster failure as completion efficiency. The [portfolio](../../docs/research_plan.md)
records the independent object-relation question and the decision after this batch.
The [account](account.md) reports completed outcomes, query use, trace diagnosis
and measurement limitations. The [results ledger](results.json) is complete: all four episodes have usage,
boundary review, causal review and exact replay.

Start and prepare a fresh episode:

```sh
.venv/bin/python scripts/episodes/start_pose_preview_episode.py pf_v1_s01_waypoints_corrected --port 8765
.venv/bin/python scripts/policy/prepare_pose_preview_policy.py runs/pf_v1_s01_waypoints_corrected
```

Dispatch the saved `policy_initial.txt` verbatim to a fresh GPT-6 Astra / medium
context, with no prior outcomes or hidden scoring inputs. Relay its JSON decisions
with the existing `scripts/policy/relay_policy.py`; prepare subsequent public handoffs with
`scripts/policy/prepare_pose_preview_handoff.py`. Preview queries and their rejected inputs
consume a decision. All calculations use `scripts/policy/policy_calc.py` in the designated
scratch folder. Keep exact policy materials and actual dispatch, inference usage,
tool audit, actions, observations and clocks. Stop at finish or the shared budget.

Completed fixed verification remains in verification_result.json, prompt_verification.json
and calculation_runtime_verification.json. Temporary fixtures and one-use verification
drivers were removed during cleanup; their original implementation is recoverable
from the recorded historical revision. Original policy episodes remain replayable.

Replay recorded motion with:

```sh
.venv/bin/python studies/pose_feasibility_v1/replay.py --run runs/pf_v1_s01_waypoints_corrected
```

That helper verifies motion/sensors/feedback/scoring, genuine current joint angles,
known-model FK against a nonmutating full-model calculation, and exact candidate
recomputation. Native cached EEF versus fresh encoder/FK differences are reported.
The executor also asserts unchanged physics on every preview. The public mechanical
model contains only robot bodies, joints, sites and known base calibration. The
solver never loads a scene, hidden object poses, contacts or native success checks.
Bounded no-solution is not global unreachability, and solutions do not certify motion
arrival, collision clearance, grasp or task completion.

After regenerating an episode's diagnostic summary, preserve missing delivery
intervals with:

```sh
.venv/bin/python studies/pose_feasibility_v1/finalize_clock.py runs/pf_v1_s02_preview
```

This changes only derived reporting, not the frozen executor or recorded actions.

The shared calculation wrapper PATH is corrected and verified in both conditions.
User-authorized amendment 002 schedules a fresh corrected first baseline, paired
with the current corrected preview. Four episodes on two states form the comparison.
The broken run records were removed at user request; only the runtime learning and
zero-policy verification remain. No third state is scheduled.
