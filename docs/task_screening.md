# Task screening record

The selection criterion is useful room to test a communication mechanism, not difficulty alone. Astra must make meaningful physical progress; repeated errors must plausibly involve command semantics, feedback, stopping or observation handoff. Sensors, controller, limits and calculation access must match across conditions. Select the evaluation task from traces before implementing a harness, then freeze before held-out trials.

## Microwave demo, retired at user request

`pilot_microwave_001` first satisfied native success at control step 1581 (command 17) and remained successful at the operator stop at step 1915. Astra chose all grasps, recovery, placement and closure actions. Its completion judgment remained unfinished. The saved native actions and simulator states support deterministic replay.

The first causal break was an unsettled starting observation: the mug dropped about 6 cm before grasping. Shared initial settling addresses that protocol error. Astra later encountered empty grasps and blocked insertion, then recovered without a task-specific executor. Those events suggest possible observation or stopping questions, but the successful episode provides no evidence of a success-rate gain from a harness. One success does not establish reliable ceiling performance.

The user requested moving to a different, harder task without a second microwave pilot. `pilot_microwave_002` was stopped after three decisions and 185 control steps. It is an aborted pilot, not a benchmark failure. Both runs received the temporary-calculation permission amendment partway through; neither belongs to frozen evaluation.

## Stacking proposal, rejected before execution

The proposed LIBERO-90 two-bowl stacking task was rejected by the user. No episode was launched. The native evaluator allows placing the lower bowl in the tray before stacking; it does not require transporting an unstable stack. Precision alone had not established a connection to the proposed interface mechanisms, so this proposal supplies no selection evidence.

## Drawer candidate, stopped at user request

`libero_90` / `KITCHEN_SCENE1_open_the_top_drawer_of_the_cabinet_and_put_the_bowl_in_it` starts a drawer-access task and requires both an open top drawer and the bowl inside it. It adds constrained articulation before object placement. The native goals and initial states are available in the pinned LIBERO revision.

Screening question: can Astra acquire the handle and make opening or placement progress, yet repeatedly persist against a constraint, lose acquisition, or act on stale geometry until the next handoff? Such a trace could motivate a generic progress or invalidation check and earlier observation. The same trace could instead show a perception, grasp-planning or controller limitation; those outcomes must not be relabeled as interface failures.

Retain the task only if the causal break is observable through permitted RGB-D or robot measurements and occurs with room for recovery. Do not add task-specific grasp, articulation or recovery logic. If direct control succeeds comfortably, or cannot make meaningful progress, discard this candidate. No main task, harness or paired protocol was frozen. The drawer opened on the first pulling attempt. At the user’s request, the operator stopped the episode at step 350 after four decisions; bowl placement was not tested. This is an aborted candidate, not a benchmark failure.


## Existing MuJoCo precision scenes

The user requested consulting LIBERO-PRO and RoboDojo failures, and using an existing MuJoCo task with the relevant failure pattern where available. The blue circular puzzle from RoboCurve was given as an example, not a requirement to recreate that hardware setup.

[RoboCurve](https://openai.robocurve.org/gpt-6-astra/) reports 2/20 successes for puzzle insertion versus 19/20 for block placement. Its [stage-3 transcript](https://openai.robocurve.org/gpt-6-astra/runs/transcripts/rig-4_76c6c1aa) includes a missed grasp, controller tracking problems, transport, then release with seating obscured and a premature completion claim. That is evidence for screening final alignment and completion verification, not proof that our Panda simulation will show the same failures. It used real YAM arms, three camera views and different execution mechanics.

[LIBERO-PRO](https://github.com/Zxy-MLlab/LIBERO-PRO) supplies configurable appearance, position, language, task and environment perturbations. These are useful distribution shifts but do not guarantee a harder manipulation mechanic for Astra. Its code was inspected at revision `eafdb809426b13153aa1e4c42d6601844217dfec`. No PRO rollout was launched.

[RoboDojo](https://github.com/RoboDojo-Benchmark/RoboDojo) was inspected at `266130a3ec41ba9b20b0e5648d2f3542f219c06c`. Its insertion task source requires depth, lateral alignment and orientation; other tasks use rings, hooks and tool slots. This provides mechanical patterns for a MuJoCo task search. No Isaac Sim installation or asset conversion was attempted.

Two existing robosuite 1.4.1 scenes were rendered with Panda, OSC_POSE, the same two RGB-D cameras and robot measurements. Their fixed 60-step verification traces both replay exactly with zero state error and no policy calls:

- `NutAssemblySquare`: fit a square nut onto a square peg. This is a simple insertion analogue. Its native completion check is comparatively coarse, based on position near the peg and gripper withdrawal, so it could be a weaker precision test.
- `ToolHang`: insert the hook frame into the stand, then thread a tool hole onto the hook and release it. The native model uses a 12 mm mount opening and a 7.5 mm frame shaft, before the second constrained insertion. Its scorer checks assembly geometry and tool-hook contact, alignment and insertion. The existing geometry and controller are retained.

ToolHang is the preferred next screening candidate because it has two physical alignment transitions and stronger native seating checks. It is a mechanical analogue of the reported failure class, not a reproduction of RoboCurve or a claimed RoboDojo score. Pilot traces must still show meaningful progress and repeatable, sensor-observable errors connected to command execution or handoff before it becomes the evaluation task. No task or harness is frozen.
