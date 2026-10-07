# ToolHang: first mechanism comparison

The six scheduled episodes are complete and replay exactly. Timed waypoints, deadline gating and early-arrival gating each achieved **0/2 full native successes**. This does not support the predicted success benefit of robot-arrival guards on these two starts. It also supplies no successful-completion efficiency comparison. The broader FYP remains active: the next question must address the observed measurement boundary rather than enlarge this batch.

## Question and design

The FYP asks which communication rules help a foundation model control a robot more effectively. Success, calls, time and cost are measured separately. Astra owns grasp, alignment, phase order, recovery and permitted temporary sensor calculations; Sol owns the simulator, generic executor and analysis.

The requested LIBERO microwave pilot reached native success. Two subsequent native ToolHang pilots yielded one success and one motion-budget failure, with empty grasps, waypoint non-arrival and blocked insertion. These supported a narrow H3 hypothesis: gating later waypoints on measured robot settling and returning observations on non-arrival might improve complete task execution.

The comparison was selected before implementation and frozen before evaluation. All conditions use the same Panda OSC_POSE controller, 256-pixel RGB-D/calibration/robot sensors, Astra medium, temporary calculation access and limits of 30 returned decisions / 2400 control steps at 20 Hz. Timed control executes every requested waypoint duration; deadline gating cancels following waypoints if settling fails; early-arrival gating also exits once measured settling passes. None measures grasp acquisition or object seating. Physics pauses during model inference.

The user reduced the original four-state plan to two states before any completed held-out outcome, after a partial first-baseline trace was visible. Both amendments and original protocols remain recorded. Two starts are the default for subsequent experiments; a third requires a specific uncertainty recorded before launching it. Three conditions share each start, so six episodes are not six independent placements.

## Outcomes and resources

| Start / condition | Final frame / tool checks | Decisions | Inference requests | Simulated s | Native policy s | API-equivalent USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 / timed | Pass / fail | 28 | 56 | 102.00 | 543.970 | 4.309184 |
| 1 / deadline | Fail / pass | 21 | 45 | 99.00 | 344.068 | 4.195272 |
| 1 / early arrival | Fail / fail | 20 | 41 | 78.95 | 261.645 | 2.526734 |
| 2 / timed | Fail / fail | 22 | 45 | 94.50 | 399.099 | 3.780594 |
| 2 / deadline | Fail / fail | 23 | 48 | 100.00 | 341.974 | 4.377322 |
| 2 / early arrival | Fail / fail | 27 | 58 | 69.45 | 460.063 | 3.972314 |

Each condition's descriptive 95% Wilson interval is [0, 0.658]. This small sample cannot establish equivalence, population success rates or cross-task generality. All six outcomes remain in their scheduled denominators. Pilots informed selection and are excluded.

Early arrival consumed 23.05 and 25.05 fewer simulated seconds than timed control, but its inference differences were -15 and +13 requests; native policy time differences were -282.325 and +60.964 seconds. Deadline differences were -11 / +3 requests and -3 / +5.5 simulated seconds. These are resources consumed in failed episodes, not faster completion or preserved reliability. No successful-pair resource ratio exists.

Native policy durations include failed turns but exclude operator waits and response delivery. Episode host timings use `time.monotonic()` and include large interruption/orchestration effects; they are not UTC timestamp differences. The second deadline's recovered elapsed origin is approximate. These host totals cannot support a speed claim. Token-derived costs use the recorded standard API rates as an equivalent estimate; native account charges and unrecorded failed-request costs are unknown.

## What failed

The first timed baseline recovered an empty grasp, assembled the frame, and physically suspended the correct larger tool hole. Its center was 9.68 mm from the hook line and insertion was 2.51%, against native limits of 6.75 mm and more than 5%. Astra reported completion despite those failed geometric checks. Visible suspension was real partial progress.

The first deadline run hung the tool correctly but never assembled the frame. Its final frame tip/base distance was 11.96 cm, against 5 cm, and its shaft was outside the stand walls. The first early-arrival run did assemble the frame, then lost it during wrist recovery with arm/frame contact and joint-bound proximity. Astra correctly reported that episode incomplete. Native public readings omitted joint positions while exposing joint velocities; no sensor field changed mid-study.

The second deadline run recovered a grasp, placed the shaft between the stand walls but about 12 cm from the base, then displaced it during withdrawal. Recovery failed and Astra accurately stopped. The second early-arrival run released an upright frame beside the stand, then lost a tool whose larger hole had not advanced beyond the hook endpoint. The tool remained supported on the gripper hand during withdrawal, then fell to the table. Astra correctly judged overall failure but incorrectly described the frame as assembled.

The second timed run recovered an empty grasp and a frame slip despite accurate robot-pose arrival. It released a shallow frame and contacted it during obstructed withdrawal. Finally, the tool was physically suspended by its **smaller hole**, while Astra described the larger hole. The larger hole did not contact the hook; frame depth and wall checks also failed. The tool-hanging subclaim and full completion judgment were inaccurate.

These are different physical failures. Pose arrival, finger opening, upright appearance and image overlap do not certify the intended object relation. The guard can prevent automatic within-command advancement after non-arrival, but Astra can still issue a new release command after a blocked motion. It does not choose a better grasp, verify hole identity or preserve whole-arm clearance.

## Scorer audit and reproducibility

The installed scorer matches official robosuite v1.4.1 after line-ending normalization. Its three success methods match structurally. A private saved-state audit agrees with the adapter and every logged final outcome: the successful pilot passes both checks, the first timed baseline passes frame assembly, the first deadline passes tool hanging, and earlier saved states in the first early-arrival run pass assembly. No stuck-false check or wrapper mismatch was found. Full native success requires frame assembly **and** hanging through the larger hole. Strict line/depth tolerances can reject visible suspension; this partial physical behavior is reported alongside the fixed primary score. The release test only checks fingerpads, so it is not a complete robot-support certificate.

All six held-out trajectories reproduce every saved simulator state with zero error. Matched initial simulator states and actual starting policy pixels/depth/calibration/proprioception are identical within each pair. Frozen source/material hashes, budgets, runtime versions and Astra medium settings pass the recorded checks. Every exported policy tool input and calculation source/output was manually reviewed. This is an instruction/audit boundary, not OS isolation.

Usage interruptions were retained in the first deadline and last timed episodes. The latter resumed the same context and original live simulator. The second deadline needed verified reconstruction after its process disappeared; its checkpoint agrees exactly with the completed saved trajectory. No start, state or budget was silently replaced. Videos are retained locally; deterministic action replay needs no model access.

Reproduce the result with `.venv/bin/python scripts/analyze_study.py`; audit scoring with `.venv/bin/python studies/tool_hang_v1/scorer_audit/audit.py`. For any run, use its `outcome.json` replay command. [Results](../studies/tool_hang_v1/results.json), [scorer audit](../studies/tool_hang_v1/scorer_audit/audit.json), and the dated [status history](experiment_status.md) retain detailed evidence.

## Revised explanation and next test

Robot-arrival guards change command execution, but the predicted full-task benefit is unsupported here. The revised hypothesis is that a useful exit/correction vocabulary needs a policy-chosen object relation that can actually be measured, with explicit loss/uncertainty, rather than treating an EEF target as a placement certificate. This does not imply a tracker can repair wrong hole selection or an incorrect target.

The next necessary test is a **zero-Astra offline measurement-feasibility audit**, recorded in [the decision](../studies/object_feedback_feasibility/decision.md) before implementation. Existing public pixel selections and replayed RGB-D streams will test whether generic correspondence can measure a model-selected surface point reliably enough for bounded translation feedback. If not, reject that route before spending on another policy comparison. If it passes, define and freeze a new matched protocol using two new starts, shared processed measurements and the same underlying controller. H1 and H4 remain open; this initial batch does not finish the broader project.
