# Candidate model-to-robot harness

**Status:** initial design conjecture, not a required schema or established solution. The experiment in [research_plan.md](research_plan.md) may revise or reject it.

## Initial conjecture

A slow model might control a robot better if it can specify what task relation matters, what the executor should measure during motion, and what evidence should end or invalidate a command. The harness also determines which observations return to the model and when it gets another turn. The slide's H1-H4 are four hypotheses about these choices, with paired tests and failure criteria described in [research_plan.md](research_plan.md); they do not prescribe four robot action phases.

The theory-to-experiment-to-theory loop is: state what each proposed mechanism should fix; inspect failures with direct control; test the smallest plausible harness and strong alternatives; then retain, change, or discard mechanisms based on paired evidence. A better interface might be simpler or structured differently from this draft.

## Delegation boundary

Depending on the tested design, the executor may update a declared target from fresh sensor data, use the same underlying robot controller used by the baselines, apply speed and workspace limits, check declared exits, and hold the robot when a required measurement is lost. Each added capability is part of the harness being evaluated and should be visible in the comparison.

It may not choose the task object, destination, grasp strategy, phase order, or recovery plan. Those are model decisions. If adding task-specific code becomes necessary, record it as a change in the system being evaluated rather than hiding it inside the executor.

Only measurements actually available to the deployed condition may drive it. Robot pose can show that the gripper reached a location; it cannot prove that an object came along. A gripper-close command is not proof of acquisition. Vision may verify a visible relation but can fail under occlusion. Simulator object poses, contact truth, and reward may score or diagnose an episode; if they control the robot, that run is an oracle condition.

## What the comparison must establish

The harness might help through clearer command semantics, correction during motion, evidence-based stopping, observation delivery, or fewer model calls. A longer command alone could also explain a gain. The [research plan](research_plan.md) specifies direct pose and waypoint comparisons, matched controls, and ablations. A whole-harness success-rate difference cannot identify an individual mechanism by itself.

Efficiency is a valid primary outcome even if direct control succeeds. For example, earlier return on a reached target or blocked motion could remove idle execution and enable a useful next decision; longer bounded execution could reduce observation overhead. The model still chooses grasps, targets and recovery. A speed claim must use verified completion, retain all failure outcomes, distinguish simulated motion from elapsed inference and execution time, and compare with a credible waypoint baseline under matched limits. Select the mechanism from traces rather than assuming that longer commands or more feedback improve speed.

Good initial conditions are those where a target changes during execution or a physical event needs verification. A static pick-and-place task with near-perfect pose-command success has little room to show a gain. Precise insertion may need contact sensing or control that the first interface does not provide. Failure on such a task should not automatically be attributed to the model.

## Open design questions to answer with traces

- Which feedback signals are available and useful during execution?
- Can the executor keep those signals valid through the motion?
- Would a completion or invalidation check fire for the right physical reason?
- Can a longer command reduce model calls without making the robot persist in a bad plan?
- What happens when the target is occluded, moves, or changes appearance?

Pilot traces should guide the command schema and observation handoff before they are frozen for evaluation. Generality across tasks, models, or hardware must be measured rather than assumed from the design.

## Current implementation boundary

The implementation exposes direct absolute poses and up to four model-selected waypoints through the standard OSC_POSE controller. Measured waypoint guards are now implemented and verified in simulator traces; see [phase_execution.md](phase_execution.md). Robot pose feedback realizes a fixed requested pose in every condition. This tests transitions and exits, not sensor-relative correction during motion. No held-out policy comparison has yet measured a benefit.

The first microwave pilot achieved native task success after model-selected grasp and insertion recovery. A wrist load or finger reading alone did not establish acquisition. Its unsettled initial measurement prompted a shared settling correction. No harness benefit has been measured, and H1-H4 remain untested. The user requested a different task; screening must establish an interface-related failure before the main task is selected. See [sensor_audit.md](sensor_audit.md) for the actual sensor boundary.

Astra may perform logged temporary calculations from the same policy-visible sensors in every condition. Those calculations select its own targets and waypoints; they do not modify the executor. See [policy_boundary.md](policy_boundary.md).

Native robosuite precision scenes reuse the same pose/waypoint executor and sensor handoff. The environment adapter supplies replay state and private benchmark scoring; it adds no grasp, alignment, insertion or recovery routine. Two ToolHang pilots now support the [task and mechanism selection](task_selection.md), recorded before harness implementation.

The first ToolHang pilot succeeded after recovery. Its first frame grasp reached the requested closing pose but acquired nothing; its first tool grasp advanced through closing after substantial waypoint non-arrival. The second pilot repeated non-arrival and blocked motion, assembled the frame, then failed at tool placement within budget. A generic measured transition or earlier observation can test an execution failure class; it cannot select better grasp geometry or certify seating. This is a pilot-derived explanation, not an evaluated benefit. The selected mechanism retains robot decisions with Astra.

The first held-out timed-baseline trace also separates robot arrival from task verification: after an empty grasp retry and frame assembly, Astra released the correct tool hole onto the hook but returned `finish` with shallow, off-axis suspension that failed the native placement criterion. The initial guard study does not measure the object relation needed to certify that final geometry. This observation is a diagnostic limit of the proposed measurement vocabulary, not yet a comparative result; the full frozen study remains incomplete.

The first held-out matched block exposes three boundaries for this vocabulary. Pose arrival does not certify the frame/stand relation, physical tool suspension does not guarantee sufficient insertion, and an EEF target does not specify whole-arm clearance. A wrist recovery can destroy completed assembly while chasing a pose. The second matched block is still underway; these are diagnostic observations, not a demonstrated comparative benefit or a frozen follow-up design. Any added relation check, invalidation rule or joint feedback must receive a separate hypothesis and matched test.
