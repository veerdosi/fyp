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
