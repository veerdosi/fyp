# Empirical account

Current through 2026-10-14. Detailed protocols, outcomes, clocks and verification
belong to the linked study accounts; this is the single project-level results index.
The [research plan](research_plan.md) contains the next decision.

## Completed comparisons

| Study | Observed outcome | Supported conclusion |
| --- | --- | --- |
| [Arrival guards](../studies/tool_hang_v1/account.md): two starts, three conditions | Timed, deadline and early-arrival each 0/2 full successes | No demonstrated task benefit here; common placement failures and small samples leave wider benefit unresolved |
| [Empty-closure handoff](../studies/tool_hang_v2/account.md): two starts, two conditions | Guarded 2/2, timed 0/2; only second pair has verified matched prompts | Retain narrow invalidation behavior; one clean pair cannot establish general reliability or speed |
| [Endpoint pose query](../studies/pose_feasibility_v1/account.md): two corrected starts, two conditions | Baseline 1/2, query 0/2; all four queried candidates solved | No demonstrated contribution; no unsupported-target warning was delivered, so warning avoidance was untested |

The arrival study's official scorer audit agrees with its recorded outcomes, and
re-executing both original pilot command sequences reproduces their original
success/failure exactly. No physical-execution regression or stuck-false check was
identified. The pose query is retired from current allocation. No replacement
state, extra query variant or repeated empty-grasp experiment is scheduled.

In the clean empty-closure pair, two interrupts cancel 105 requested steps / 5.25
simulated seconds, including two empty lifts; Astra chooses both recoveries. The
guarded run uses 59 inference requests and 108.75 simulated seconds; the failed
timed run uses 53 and 103. This is not faster completion. The first guarded success
has no interrupt, and its pair is prompt-confounded. No study has a jointly successful
pair supporting a successful-completion resource ratio. Full tables remain in the
accounts/results JSON, including uncertainty, costs and interrupted-clock limits.

## Pilots and task selection

The retained LIBERO microwave pilot succeeds after empty-grasp and blocked-insertion
recovery. Its first observation preceded a roughly 6 cm settling drop; later starts
include fixed settling. That setup fault is not a general Astra limitation. The user
retired the task. [Its original records](../runs/pilot_microwave_001/outcome.json)
remain separate from paired results.

Two native ToolHang pilots produce one full success and one motion-budget failure,
with useful grasp/rotation/placement progress and repeatable empty grasps, non-arrival
and blocked insertion. They motivated the original narrow arrival study. They do not
establish a 50% success probability and are excluded from held-out comparisons.
[Selection and pilot evidence](../studies/tool_hang_v1/account.md#task-selection)
identify why the task was originally useful and why a new task is now planned.

## Measurement and diagnostic screens

| Screen | Result | Decision |
| --- | --- | --- |
| [Local point tracking](../studies/object_feedback_feasibility/results.json) | Visible coverage 63.1%, accepted error p95 9.28 mm, occluded false-valid 25.9% | Fails frozen measurement gates |
| [CoTracker3](../studies/object_feedback_learned/accuracy_result.json) | Coverage 97.7%, error p95 5.55 mm, false-valid 24.8% | Fails precision/loss gates; runtime p95 2.17 s also misses Sol's original 0.4 s realtime criterion, which the project does not require |
| [Depth uncertainty](../studies/object_feedback_depth/attempt_001/result.json) | Primary coverage 77.63%, error p95 4.89 mm, false-valid 16.52% | Reject tested precision estimator; cross-camera agreement does not certify point identity |
| [Robot feedback](../studies/robot_feedback_modalities/monitor_result.json) | Empty closure exposes contradictions; load/progress miss upstream-arm contact | Supports narrow empty invalidation, not seating or whole-arm safety certificates |
| [Rotation/IK diagnostic](../studies/mechanism_selection/discriminator_result.json) | Four inspected calculations reproduce; bounded search solves 14/17 targets | Separates arithmetic from robot geometry; no global unreachability claim |
| [Placement discriminator](../studies/placement_error_discriminator/account.md) | Five latest calculations reproduce; three initial approaches retain comparatively stable attachment | No simple arithmetic fix or universal grasp-drift explanation; contact and placement remain distinct |

These reuse observed traces and spend no new Astra calls. Failed measurement
prerequisites do not falsify all H1 feedback correction. The alternative tracker
follow-up was retired at the user's request; no new tracker work is scheduled.

## Cross-episode findings

[The returned-reason audit](../studies/cross_episode_failure_audit/account.md) reviews
394 command reasons across all 16 retained ToolHang episodes. Earliest incidents
are ten missed acquisitions, four cancelled approaches, one slip and one blocked
insertion. In the 12 unsuccessful episodes, 11 end with unresolved placement,
release or recovery; one is dominated by joint-limited reorientation/collision.
Five unsuccessful episodes claim full success, four acknowledge failure, one
reports uncertainty and two reach a budget stop without finish.

Clear contradictions often prompt useful recovery. Interpreting support, apparent
hole overlap and release evidence is less reliable. Two overstated finishes involve
real suspension through the correct hole that misses stricter native geometry;
observability and task-score alignment remain rival explanations. These are manual
retrospective counts across protocols and repeated starts, not independent failure
probabilities, hidden reasoning or unique causal attribution.

## Revised explanation

Robot arrival, finger opening and visible upright support answer different questions
from successful object placement. The next study must distinguish feature/geometry
estimation, conversion into robot commands, physical execution and verification.
Select a new task with an explicit observable goal and a controlled contrast before
building another module. Object-relation representation is a candidate; collision
and contact prototypes are not the main next study. See [the next decision](research_plan.md#next-decision).
