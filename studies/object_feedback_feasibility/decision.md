# Next necessary test: public object-point measurement feasibility

Recorded on 2026-10-08 after all six ToolHang v1 outcomes, scorer audit and replay verification, before implementing this measurement prototype. This is development using already observed traces, not new held-out evidence or a policy-success experiment.

## Why this test

Arrival guards did not improve full native success (0/2 in every condition). Accurate gripper motion coexisted with slip, shallow insertion, wrong hole selection and misleading projected overlap. A proposed object-point feedback mechanism first needs a reliable measurement source. Spending on another Astra batch before testing that source would not isolate the hypothesis.

Question: can a generic RGB-D correspondence estimator track a policy-selected visible surface point at the precision required for bounded translation correction, while marking occlusion or loss as unknown?

## Frozen feasibility scope

Use every pixel query from all six v1 episodes, retaining wrong/background selections as actual queries. For each query, reconstruct the following recorded motion command as a 20 Hz image/depth/calibration stream until its end or the next sensing decision. Both existing matched starts are included. Do not choose only favorable grasps, cameras or segments after seeing estimator results. No additional Astra calls, policy episodes or third starting state are needed.

The estimator may consume only 256-pixel RGB, ideal metric depth, calibration and the query pixel. It must not read object names/poses, collision geometry, segmentation or native scores. Private rigid-body transforms and segmentation may supply a separate scoring reference and visibility label, never estimator inputs. Compare the tracked world point with the rigidly transported initial surface point; report that geometric point may differ from the intended semantic tip or virtual hole center. Count invalid initial queries and wrong semantic selections separately instead of silently repairing them.

Start with generic local correspondence and forward/backward consistency, with depth-based world coordinates and explicit invalid/lost results. Freeze estimator parameters before scoring the complete cohort. Report coverage as well as conditional accuracy so rejecting everything cannot pass.

Feasibility gate: on reference-visible samples, at least 80% accepted coverage and accepted 95th-percentile world-point error at most 3 mm; on reference-occluded/lost samples, false-valid rate at most 5%. Report results separately for both cameras, translations, rotations and both starts; a missing category cannot establish its feasibility. These are development gates, not task-success evidence. If they fail, revise or reject this route before any main policy comparison; preserve the first audit and any later parameter revisions separately.

## Conditional next mechanism

Only after a passing measurement audit, consider an Astra-specified surface anchor/world target under fixed-orientation translation. A bounded executor could update translation from measured anchor error and return on convergence, loss or deadline; Astra would choose anchors, desired relation, grasp, rotation and recovery. The executor must have no object-specific task routine or oracle access. Wrong identity/target selection remains a policy failure.

Before a main comparison, define a new frozen protocol with two new matched starts. Give direct control and feedback control identical raw/processed sensing, computation access, controller, budgets and model settings. A sampled-target versus continuously updated target control would isolate feedback, with success, model calls, time and cost retained for every scheduled outcome. Include a second suitable task only when it tests the same generic executor/command vocabulary. Do not launch the next policy batch on an assumed passing result; first complete the feasibility audit and freeze the subsequent protocol.

## Interpretation amendment before implementation

The user correctly challenged treating all six failures as rejection of arrival gating. They are two correlated placements with common object failures; the guard effect on full success remains unresolved. Before this prototype is implemented, re-execute both original pilot command sequences under the current timed baseline to rule out a physical execution regression, and distinguish that check from changed prompts/feedback and policy decisions. See [the recorded regression decision](../tool_hang_v1/baseline_regression_decision.md). The original proposed measurement gate remains preserved; it is not a reason to abandon arrival gating or rerun more starts by default.

The prerequisite command re-execution audit has now passed for both pilots, with exact actions/states and original outcomes under the current baseline. Physical execution regression is ruled out for these sequences; policy behavior and start difficulty remain unresolved. Resume this zero-inference feasibility audit as a complementary measurement question. Retain arrival gating as unresolved, and do not interpret a passing tracker gate as evidence against it.

## How the six outcomes determine this test

The comparison distinguishes a measured robot event from the intended object event. The first timed run assembled the frame but failed native tool placement; the first deadline run passed tool hanging but never assembled the frame. The first early-arrival run assembled the frame and then lost it during recovery. The second-start runs exposed shallow/outside seating, slip, displacement on withdrawal and smaller-hole selection. These failures give object measurement a plausible role while limiting what it could explain. A correspondence estimator cannot supply a better grasp, choose the larger hole, infer a hidden insertion depth or plan whole-arm clearance. This audit asks whether its input measurement is usable, before making any claim that feedback changes those failures.

Early-arrival control consumed less simulated motion on both starts, but calls and policy time changed in opposite directions. Those failed episodes do not support faster completion. The broader guard effect remains unresolved because both starts share difficult placement stages and no condition completed the whole task. The next policy comparison must retain verified success alongside resource use, and must not count tracker accuracy as manipulation success.

## Reconstruction and reference amendment before estimator scoring

The first reconstruction attempt rendered saved end-of-step states. It failed exact image reconstruction. A subsequent action replay also differed after force-restoring the initial state. Native `Observable.update` advances its sampling timer even when forced, so that restore changes camera sampling phase without changing the replayed physics. A diagnostic using the original seeded reset, without forced updates, reproduces both starting camera frames exactly. Preserve failed drivers and checks in `reconstruction_diagnostic/`; match the original episode initialization and require exact RGB, depth and calibration at every queried snapshot before scoring.

Camera sampling also occurs inside the native control step. Public calibration is recorded at command handoff, so moving wrist-camera calibration can differ from calibration at image sampling. Private scoring must capture geometric references when each original camera sensor samples, without changing its return values or timing. Report image-time geometric error and current-step error separately, including camera age and initial query calibration error. The 3 mm gate applies to the current-step world point needed by a feedback executor. Neither image-time truth nor synchronized private calibration may enter the tracker. No estimator scoring has occurred before this amendment, and the estimator parameters and feasibility thresholds remain unchanged.
