# Pose-feasibility query: two-start paired study

This is a computational planning aid, not a new stop rule. Astra medium receives
the same public robot/sensor data and logged calculation access in both conditions.
The query condition additionally has an optional robot-only bounded IK command.
It neither moves the robot nor selects a target/recovery. Both conditions share
ordinary waypoint execution and the existing explicitly armed empty-closure behavior.

The [prospective mechanism protocol](../mechanism_selection/mechanism_protocol.json)
and [implemented freeze](protocol.json) specify two new matched starts / four episodes.
Run the declared order. Do not replace failures, add another start by default, or
report faster failure as completion efficiency. The [portfolio](../../docs/mechanism_portfolio.md)
records the independent object-relation question and the decision after this batch.

Start and prepare a fresh episode:

```sh
.venv/bin/python scripts/start_pose_preview_episode.py pf_v1_s01_waypoints_corrected --port 8765
.venv/bin/python scripts/prepare_pose_preview_policy.py runs/pf_v1_s01_waypoints_corrected
```

Dispatch the saved `policy_initial.txt` verbatim to a fresh GPT-6 Astra / medium
context, with no prior outcomes or hidden scoring inputs. Relay its JSON decisions
with the existing `scripts/relay_policy.py`; prepare subsequent public handoffs with
`scripts/prepare_pose_preview_handoff.py`. Preview queries and their rejected inputs
consume a decision. All calculations use `scripts/policy_calc.py` in the designated
scratch folder. Keep exact policy materials and actual dispatch, inference usage,
tool audit, actions, observations and clocks. Stop at finish or the shared budget.

Fixed verification is retained under `fixed_waypoints`, `fixed_preview` and
`fixed_query_budget`. The query preserves live state exactly; subsequent paired
actions and states match exactly; the public calculation and returned query agree;
raw encoder inputs, robot FK and joint bounds match; invalid/final queries consume
budget. Both motion fixtures replay exactly, including sensors, feedback and scoring.
The zero-decision prompt fixtures verify byte-identical common text after paths and
the declared capability paragraph are normalized. All verification uses zero Astra
requests. Re-running a fixture requires fresh directories; old artifacts are retained.

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

The shared calculation wrapper PATH is corrected and verified in both conditions.
User-authorized amendment 002 schedules a fresh corrected first baseline, paired
with the current corrected preview. Four episodes on two states form the comparison.
The broken run records were removed at user request; only the runtime learning and
zero-policy verification remain. No third state is scheduled.
