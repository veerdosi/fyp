# What the robot-interface experiments have established

The FYP asks which communication mechanisms help a foundation model control a robot more effectively. The evidence so far supports a narrow invalidation mechanism and exposes an unresolved object-relation problem. It does not establish a reliable success-rate or completion-speed improvement. The paired manipulation code and traces are runnable, and the depth uncertainty screen has completed with a negative result.

## From theory to evidence

Astra medium controlled the robot through absolute poses and short waypoints, with fresh RGB-D/calibration/robot observations between commands and logged temporary calculations. Sol owns implementation, design and diagnosis; Astra selects every grasp, destination, phase and recovery. The generic executor has no task-specific grasp or placement policy. Simulator-only state scores and diagnoses outcomes, never controlling evaluated actions. Physics pauses during inference.

The initial LIBERO microwave pilot reached native success after recovering from empty grasps and blocked insertion. Its first measurement preceded an approximately 6 cm settling drop; subsequent runs use a common 20-step settling period. The user retired the task. Two native MuJoCo ToolHang pilots then produced one full success and one budget failure, with repeated non-arrival, grasp slip and blocked seating. This selected a precision scene where direct control makes meaningful progress and interface changes might help. Pilot success is not a known 50% probability.

| Stage | Prediction tested | Observation | Research consequence |
| --- | --- | --- | --- |
| Robot-arrival handoff, two starts × three conditions | Measured pose exits prevent inappropriate advancement and improve completion | Timed, deadline and early-arrival each finished 0/2; distinct seating, grasp and whole-arm failures | No observed task benefit; wider guard effect unresolved. Arrival is not an object-relation certificate. |
| Public-point measurement development, all 212 existing queries | A visible anchor can supply precise correction feedback | Local flow failed coverage/precision/loss; CoTracker retained 97.7% visible endpoints but failed 3 mm precision and 5% loss gates | Neither tested estimator should drive precision feedback. Depth association can fail despite subpixel correspondence. |
| Depth uncertainty, same 2,757 cached endpoints | Local support and other-camera depth reject ambiguous measurements without losing usable coverage | Primary coverage 77.6%, error p95 4.89 mm, occluded false-valid 16.5%; all gates fail | Reject this estimator for correction. Camera agreement cannot certify point identity. |
| Empty-closure invalidation, two starts × two conditions | Contradicted grasp expectation can cancel an empty continuation and return control for recovery | Guarded 2/2 and timed 0/2; first pair prompt-confounded, second pair matched. Two correct interrupts on start 2 | Retain narrow invalidation/handoff behavior; completion result is encouraging but uncertain, with no efficiency result. |

The six arrival episodes replay exactly, official native scorer methods agree, and original pilot commands still reproduce one success/one failure under current physical execution. There is no identified execution regression or stuck-false scorer. Common placement failures and tiny samples prevent rejecting a general guard benefit. [The arrival account](arrival_guard_account.md) retains every outcome, resource count and scoring diagnosis.

## What the new comparison adds

In the clean empty-closure pair, guarded control completed both native checks with 28 decisions, 59 usage-recorded inference requests and 108.75 simulated seconds. Timed control used 26 decisions, 53 requests and 103 simulated seconds, then declared completion while only frame assembly passed. Its larger ring contacted the frame's grip section, its smaller ring contacted the table, and its center was 43.75 mm from the horizontal hook line (native limit 6.75 mm). This is an incorrect object relation and completion judgment, not merely a barely missed tolerance.

The guarded episode cancelled two empty close/carry continuations: 105 requested steps / 5.25 simulated seconds. Rebuilt stop geometry showed no fingerpad contacts, and Astra chose a lower frame regrasp and later a side approach for tool recovery. It also recovered a released tool that fell, then chose a different final placement. These stops demonstrate intended invalidation behavior, but the final success cannot be attributed solely to them. The first guarded success had no stop at all, so it cannot prove an interrupt benefit.

All four outcomes remain recorded. Descriptive 95% Wilson intervals are [0, 0.658] for timed and [0.342, 1] for guarded, including the confounded pair. Only one pair has matched common instructions. There are no jointly successful pairs for a completion-resource ratio. The clean guarded run consumed more requests and simulated time than the failed baseline. Interrupted host times and a failed usage-limit turn prevent an elapsed-speed claim; API-equivalent cost is not an actual account charge. [The completed empty-closure account](../studies/tool_hang_v2/account.md) contains the full table, clocks, prompt erratum and audits.

Every final trajectory replays with zero state/sensor/calibration error, and all processed feedback/scoring rows match. Both second-start episodes resumed their original policy contexts and budgets after verified action reconstruction. Retained original robot/object/scoring records and final images matched exactly; original full hidden prefix arrays were unavailable. All policy tools/calculations were reviewed against public-data boundaries. This is an instruction/audit boundary, not an OS sandbox.

## Revised theory and next decision

A useful communication contract can invalidate a contradicted expectation without taking the task decision away from the model. That is different from certifying acquisition, seating or completion. The next conjecture is that correction needs a policy-selected object relation with a usable metric measurement and explicit uncertainty. Better tracking cannot repair wrong target identity, and wrist feedback does not describe whole-arm clearance. Short command reasons help distinguish stated expectations from execution and geometric errors; they do not expose complete internal reasoning or prove causality.

The completed [depth screen](../studies/object_feedback_depth/account.md) reused the same predictions and exactly reconstructed public sensors. Surface rejection removed bad associations but lost visible coverage; temporal/camera checks rejected no additional reference-occluded points. Nineteen accepted occluded references even had corroborating other-camera depth. The tested depth configuration cannot drive precision correction. This rejects a prerequisite estimator, not H1 itself.

The [next decision](../studies/object_feedback_depth/next_test.md) selects one fixed official TAPNext++ feasibility screen and then the same-cohort accuracy audit if runnable. This tests correspondence/visibility while retaining the failed depth gates. If neither supplies usable feedback, retire this route and select a different trace-supported representation or feasibility question. No further finger-guard variation or third v2 start is scheduled. A usable development measurement would still need a separately frozen robot comparison on two new matched starts.

These are small mechanism screens, not general robot-policy benchmarking. The FYP remains active: the next experiment must resolve a new design choice, and H1–H4 can be revised or replaced. A positive result is not promised.

For runnable commands and evidence, use [the v2 README](../studies/tool_hang_v2/README.md), [paired results](../studies/tool_hang_v2/results.json) and [dated status history](experiment_status.md). All verification replays use zero Astra calls.
