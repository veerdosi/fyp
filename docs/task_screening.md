# Task screening record

The selection criterion is useful room to test a communication mechanism, not difficulty alone. Astra must make meaningful physical progress; repeated errors must plausibly involve command semantics, feedback, stopping or observation handoff. Sensors, controller, limits and calculation access must match across conditions. Select the evaluation task from traces before implementing a harness, then freeze before held-out trials.

The user's 2026-10-06 clarification also permits an efficiency-led task: direct Astra can succeed, yet take repeated sensing turns, unnecessary retries or excess execution time that a harness might reduce. Verified success remains necessary for a faster-completion claim. This broadens the selection criterion; it does not reinstate retired tasks against the user's request.

## Microwave demo, retired at user request

`pilot_microwave_001` first satisfied native success at control step 1581 (command 17) and remained successful at the operator stop at step 1915. Astra chose all grasps, recovery, placement and closure actions. Its completion judgment remained unfinished. The saved native actions and simulator states support deterministic replay.

The first causal break was an unsettled starting observation: the mug dropped about 6 cm before grasping. Shared initial settling addresses that protocol error. Astra later encountered empty grasps and blocked insertion, then recovered without a task-specific executor. Those events suggest possible observation or stopping questions, but the successful episode provides no evidence of a success-rate gain from a harness. One success does not establish reliable ceiling performance.

The user requested moving to a different, harder task without a second microwave pilot. `pilot_microwave_002` was stopped after three decisions and 185 control steps. It is an aborted pilot, not a benchmark failure. Both runs received the temporary-calculation permission amendment partway through; neither belongs to frozen evaluation.

## Stacking proposal, rejected before execution

The proposed LIBERO-90 two-bowl stacking task was rejected by the user. No episode was launched. The native evaluator allows placing the lower bowl in the tray before stacking; it does not require transporting an unstable stack. Precision alone had not established a connection to the proposed interface mechanisms, so this proposal supplies no selection evidence.

## Existing MuJoCo precision scenes

The user requested consulting LIBERO-PRO and RoboDojo failures, and using an existing MuJoCo task with the relevant failure pattern where available. The blue circular puzzle from RoboCurve was given as an example, not a requirement to recreate that hardware setup.

[RoboCurve](https://openai.robocurve.org/gpt-6-astra/) reports 2/20 successes for puzzle insertion versus 19/20 for block placement. Its [stage-3 transcript](https://openai.robocurve.org/gpt-6-astra/runs/transcripts/rig-4_76c6c1aa) includes a missed grasp, controller tracking problems, transport, then release with seating obscured and a premature completion claim. That is evidence for screening final alignment and completion verification, not proof that our Panda simulation will show the same failures. It used real YAM arms, three camera views and different execution mechanics.

[LIBERO-PRO](https://github.com/Zxy-MLlab/LIBERO-PRO) supplies configurable appearance, position, language, task and environment perturbations. These are useful distribution shifts but do not guarantee a harder manipulation mechanic for Astra. Its code was inspected at revision `eafdb809426b13153aa1e4c42d6601844217dfec`. No PRO rollout was launched.

[RoboDojo](https://github.com/RoboDojo-Benchmark/RoboDojo) was inspected at `266130a3ec41ba9b20b0e5648d2f3542f219c06c`. Its insertion task source requires depth, lateral alignment and orientation; other tasks use rings, hooks and tool slots. This provides mechanical patterns for a MuJoCo task search. No Isaac Sim installation or asset conversion was attempted.

Two existing robosuite 1.4.1 scenes were rendered with Panda, OSC_POSE, the same two RGB-D cameras and robot measurements. Their fixed 60-step verification traces both replay exactly with zero state error and no policy calls:

- `NutAssemblySquare`: fit a square nut onto a square peg. This is a simple insertion analogue. Its native completion check is comparatively coarse, based on position near the peg and gripper withdrawal, so it could be a weaker precision test.
- `ToolHang`: insert the hook frame into the stand, then thread a tool hole onto the hook and release it. The native model uses a 12 mm mount opening and a 7.5 mm frame shaft, before the second constrained insertion. Its scorer checks assembly geometry and tool-hook contact, alignment and insertion. The existing geometry and controller are retained.

ToolHang is the preferred next screening candidate because it has two physical alignment transitions and stronger native seating checks. It is a mechanical analogue of the reported failure class, not a reproduction of RoboCurve or a claimed RoboDojo score. Pilot traces must still show meaningful progress and repeatable, sensor-observable errors connected to command execution or handoff before it becomes the evaluation task. No task or harness is frozen.

`pilot_tool_hang_001` completed successfully and returned a correct completion judgment in 20 decisions, 40 actual inference requests and 92.75 simulated seconds. Replay reproduces all 1855 states exactly. It contains two empty-grasp recoveries, blocked insertion and a snagged withdrawal. In the first tool grasp, approach and descent ended roughly 9 cm from their requested poses before closing continued. That gives a testable question about measured phase transitions or earlier handoff, with longer fixed execution as a required control. The first frame miss instead reached its requested closing pose and still missed: that grasp-planning error cannot be attributed solely to duration. See [the full trace analysis](pilot_tool_hang_trace.md).

The pilot supports retaining ToolHang as a candidate under the user's broadened outcome criteria. It does not establish repeatability, an accuracy ceiling or any harness benefit. Screen a different initial state before selecting the task and mechanism. Future task instructions specify the larger tool hole to match the native scorer; no pose, grasp or recovery hint is added.
