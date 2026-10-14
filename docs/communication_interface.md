# Robot interface and measurement boundary

This is the operational reference. [The research plan](research_plan.md) selects
experiments; each study's frozen protocol is authoritative for its historical
configuration. No new relation, collision or contact-control module is selected.

## Ownership and public inputs

Sol owns research, simulator/executor code, verification and reporting. GPT-6 Astra
at medium effort owns robot decisions in fresh episode contexts, with no delegation.
Astra may write temporary sensor calculations inside its episode's `policy_compute`
directory, executed by `scripts/policy/policy_calc.py`. Code, available-input hashes,
stdout/stderr, status and timing are logged. Calculation tools, access and the
30-second per-execution limit are matched across conditions.

The policy receives 256-pixel RGB and metric optical-axis depth from `agentview`
and `robot0_eye_in_hand`, camera intrinsics/extrinsics, measured EEF position and
XYZW quaternion, joint/finger measurements and raw wrist force/torque. Later
pose-query episodes also expose genuine current joint positions and a known robot-only
kinematic model in both conditions. Earlier episodes omitted joint positions; each
saved public observation is authoritative. Pixel queries unproject selected depth;
they do not identify an object or guarantee that a pixel belongs to the intended surface.

Images use a top-left origin. The simulated camera mounting and calibration are
ideal; no deliberate sensor noise was added. Native observable sampling can differ
from a forced state restore, so strict sensor replay reproduces the original reset
and action sequence. Wrist loads include gravity, held-object weight and dynamics;
they do not certify grasp, seating or whole-arm clearance.

Object poses, object-state vectors, contacts, reward, simulator state and native
success predicates remain private scoring/diagnosis. They neither select policy
actions nor drive executor corrections. The policy restriction is an instructed
and manually audited boundary, not an OS filesystem sandbox. Saved policy inputs,
actual tool bodies and calculation sources are the evidence for compliance.

## Commands and shared controller

The standard policy returns JSON `sense`, `move` or `finish`. A move contains one
to four Astra-selected absolute EEF poses/waypoints, optional orientation, gripper
state and duration. Omitted orientation holds the measured orientation resolved
for that waypoint. Native Panda OSC_POSE executes bounded delta actions using robot
pose feedback, with unchanged underlying controller settings across conditions.

Historical episode limits are 30 returned decisions and 2400 steps at 20 Hz,
including 20 initial settling steps; 1–100 steps per waypoint and at most 200 per
command. Sense, finish and rejected commands consume decisions. Retries have no
separate quota. Per-step caps are 0.015 m translation and 0.15 rad orientation;
workspace limits remain common. Physics pauses during policy inference. These limits
are not collision checks and a reached EEF pose is not object/task success.

Every handoff supplies fresh images and execution measurements. Existing OSC feedback
and model replanning are distinct from live correction of an object-relative command.
Astra selects any new target or recovery; the executor supplies no task-specific
grasp, insertion search or plan.

## Execution conditions

| Condition | Within-command behavior |
| --- | --- |
| Timed waypoints | Execute declared duration and advance; return observations after the sequence |
| Deadline guard | Execute duration; cancel following waypoints if settled arrival fails |
| Early-arrival guard | End after settled arrival or deadline; cancel following waypoints on failed settling |
| Empty-closure guard | Cancel only an explicitly armed continuation when stable empty-sized closure contradicts the expected grasp |

Arrival requires position error at most 3 mm, orientation error at most 0.03 rad,
linear/angular speeds at most 0.005 m/s and 0.05 rad/s, and finger-speed norm at
most 0.001 m/s, for three consecutive samples after at least ten executed steps.
These are robot execution tolerances, not the scene's insertion tolerances.
All conditions receive the same robot-derived execution reports within their study.

The retained empty rule requires closed-command finger opening at most 2.9997 mm,
finger speed at most 1 mm/s and three samples after ten steps. Load/progress flags
remain advisory. Non-empty closure does not certify acquisition or placement.
[The fixed prototype results](../studies/robot_feedback_modalities/guard_verification_result.json) and
[paired study](../studies/tool_hang_v2/account.md) separate fixed verification from
policy outcomes and the first-pair prompt confound.

The completed pose-query condition adds optional `preview` of one to four candidate
EEF poses. Bounded IK reports solutions, residuals, joint margins and runtime; a query
uses a decision but advances no physics. It checks robot-only endpoint geometry,
not paths, contact, collision, grasp or task relations. Baseline has the same robot
model/helper and logged computation access. [Its account](../studies/pose_feasibility_v1/account.md)
reports no observed contribution on the two starts.

## Reproduction and accounting

Every policy run retains configuration/revision, exact inputs and outputs, tool and
calculation records, public observations, actions, state trajectory, outcome and
replay checks. Private diagnostics stay separate from policy folders. Actions reproduce
physics, not stochastic model decisions. Match the study's replay helper when camera
sampling or genuine encoder checks matter; see [the README](../README.md).

Record native inference/tool time separately from simulated motion, execution,
delivery and operator/host elapsed. Count inference requests separately from robot
decisions. API-equivalent cost uses logged tokens and recorded rates; actual billing
is unknown. Missing intervals stay null; recovered clocks and unavailable original
hidden prefix arrays remain reported limitations. Keep fault records in raw evidence.
