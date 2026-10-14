# Returned reasons and recurring failures across ToolHang episodes

Retrospective audit by Sol, 2026-10-14. All 394 short returned command reasons in
the 16 retained genuine Astra ToolHang episodes were read, alongside their public
execution reports, the previous per-episode causal reviews and terminal scoring.
The two pilots and every scheduled outcome of v1, v2 and the corrected pose-query
batch are included. Fixed-command replays are verification, not additional policy
episodes. Removed episodes are excluded. No new Astra calls were made.

Reasons are self-reports. They do not expose complete internal reasoning and do
not establish that a stated belief caused an action. This audit identifies
testable explanations for observable behavior, not intrinsic model mechanisms.
Private simulator measurements remain offline scoring/diagnosis, never policy or
executor inputs. The audit additionally inspected the final public agent views of
v1 start-2 direct, v2 start-2 timed and both pose-query start-2 episodes.

## Counting method

The unit is an episode, not a sentence, waypoint or retry. The first incident is
the first unsuccessful manipulation or cancelled approach. Numerical non-arrival
alone is not a failed grasp. An incident can recover; terminal stage records the
unresolved physical problem without claiming a unique underlying cause.

This is manual retrospective coding by one reviewer, with explicit episode and
decision references in [coding.json](coding.json). There is no independent coding
agreement estimate. Counts span different protocols and repeated matched starts;
they are not independent samples or pooled reliability estimates. The first v2
pair remains prompt-confounded and is included descriptively, not causally.

## Earliest incidents

| First incident | Episodes / 16 | Interpretation |
| --- | --- | --- |
| Missed acquisition | 10 | Empty initial grasp or first attempted lift; geometry and timing often change together during recovery |
| Cancelled non-arriving approach | 4 | Guard returns control before the initial grasp sequence finishes; not four failed grasps |
| Attachment loss during rotation | 1 | Frame initially lifts, then slips during transport/reorientation |
| Blocked frame insertion | 1 | Initial acquisition succeeds; insertion is the first manipulation failure |

The four successful episodes also have early incidents. Early acquisition
problems are common, but that does not make acquisition the best explanation for
terminal failure or justify repeating the empty-grasp experiment.

## What remained unresolved

There are 12 unsuccessful episodes. Their terminal unresolved stages are five
tool-placement/release/recovery failures, two frame-placement/release/recovery
failures, four with both object relations unresolved, and one dominated by
joint-limited reorientation followed by a whole-arm collision and failed recovery.
Thus 11/12 end with unresolved placement/release/recovery after useful progress.
These stages do not distinguish incorrect perception, incorrect target geometry,
controller/contact constraints, insufficient observations or exhausted budgets.

| Final judgment in the 12 failed episodes | Count |
| --- | --- |
| Unqualified full-success claim disagrees with native score | 5 |
| Correct overall failure acknowledgment | 4 |
| Finish explicitly reports seating uncertainty | 1 |
| Budget stop without a finish declaration | 2 |

The five overstated finishes are v1 start-1 direct, v1 start-1 deadline, v1 start-2
direct, v2 start-2 timed and pose-query start-2 preview. This is not five identical
perceptual errors. In v1 start-1 direct and pose-query start-2 preview, the tool is
genuinely released and suspended through the correct larger hole, but shallow or
off-axis engagement fails frozen native tolerances. In v1 start-2 direct the
smaller hole actually contacts the hook despite larger-hole descriptions. In v2
start-2 timed the final tool contacts the wrong frame section and table. The
start-1 deadline run correctly hangs the tool but accepts an unseated frame.

## Patterns in the stated expectations

1. Clear acquisition contradictions often produce useful updates. For example,
   corrected pose-query baseline start 1, decision 3, says the first closure was
   empty and lowers the grasp. V2 timed start 2, decision 6, observes empty fingers
   and a displaced frame, then regrips and splits the rotation. These are concrete
   counterexamples to a general explanation that Astra never uses feedback.
2. The relationship between visible support and correct placement is less reliable.
   V1 direct start 2, decision 21, says the hook visibly passes through the larger
   hole; the final private diagnosis identifies the smaller hole. V2 timed start 2,
   decision 24, describes the hook through the larger opening; reached EEF targets
   do not establish the required final tool relation. Pose-query preview start 2,
   decision 28, accepts a supported frame and suspended tool despite native seating
   and engagement failures. These are behavioral mismatches, not proof of a single
   internal spatial-reasoning defect.
3. Release is an intervention, not a passive check. Pilot 2 decision 24 predicts
   support, followed by decision 25 acknowledging a fall. V2 guarded start 2
   decisions 20/21 repeat that pattern, then recover successfully. Pose-query
   preview start 2 decisions 11–13 acknowledge that the open hand carries the frame.
   Finger opening, EEF arrival and projected overlap do not guarantee support transfer.
4. Motion constraints are real competing explanations. V1 phase start 1 decisions
   14–19 include a joint bound and a recovery sweep that destroys previously valid
   assembly. Corrected pose-query baseline start 1 decisions 10/11 change an
   obstructed crossing into a successful higher route. A reasoning intervention
   cannot be credited merely because it adds a stronger controller or planner.
5. Fresh measurements are already common. The returned reasons repeatedly request
   new shaft, hole and hook measurements after rotation, slip or contact. The five
   latest logged calculation outputs reproduce exactly, as do the four earlier
   inspected rotation calculations. That weakens a simple arithmetic-execution
   explanation, without certifying feature identity, estimated geometry or targets.

## Research implications

The leading behavioral question is how Astra translates observable evidence into
a belief about an object's relation and the next physical action. Object-centric
representation is one possible intervention; this audit has not selected it as a
proven remedy. Competing explanations include ambiguous observations, stricter
native scoring than apparent visible completion, wrong feature selection, action
conversion and actual contact/controller limitations.

A stronger next study should distinguish those explanations before adding an
alignment, collision or force-control module. Use a new task with an observable,
explicit goal and controlled changes of viewpoint or object/grasp orientation.
Keep task difficulty sufficient for action errors but avoid making millimetre-scale
contact and hidden scoring tolerances the dominant confound. Predeclare one
manipulation of interest; do not vary camera, grasp, geometry and controller together.

Measure selected features/geometry, requested motion, achieved motion and the
post-action relation separately. If Astra selects the wrong feature, examine
grounding/observation support. If its feature estimate is coherent but the requested
motion would produce the wrong relation, examine action representation. If the
requested geometry is coherent and execution diverges, examine embodiment/contact.
If placement is wrong and Astra accepts it, examine evidence and verification.
Allow unresolved/mixed classifications; retrospective labels alone are not causal
proof. Controlled prospective comparisons must decide between the explanations.

No collision or contact prototype is selected for implementation pending task
selection and a discriminating diagnostic protocol. The earlier zero-Astra
wrist screen is preserved as a possible prerequisite, not the main research study.
No new policy batch is scheduled or run by this audit. Future comparisons retain
two matched starts by default and fresh medium-effort Astra contexts used only in
actual robot episodes. Short diagnostic episodes must still execute robot decisions,
not repurpose Astra as a project advisor or an offline question-answering evaluator.

The microwave pilot is supplementary: its initial settling drop is a setup fault,
not a stable Astra limitation. After that, its reasons identify empty body grasps,
switch to a handle grasp, react to entrance contact and revise placement before
native success. It reinforces the evidence for useful recovery, but is excluded
from ToolHang counts because task and settling protocol differ.

Reproduce the ledger and counts with:

```sh
.venv/bin/python studies/cross_episode_failure_audit/analyze.py
```

[results.json](results.json) contains the counts, original-command paths and source
hashes. [coding.json](coding.json) retains each episode's classification and decision
references. Exact commands, public inputs, measurements and fault records remain
in the original run folders; this report does not duplicate them. Source changes
require reviewing classifications again. Original episodes and scores are unchanged.
