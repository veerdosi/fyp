# Literature review: interfaces between foundation models and robots

This review is a map of prior approaches and failure modes, not a commitment to a benchmark or interface. **Frontier model** names the general class; **Astra** names the first model we may test. For the runnable next step, see [research_plan.md](research_plan.md).

## The question left open by current systems

Frontier multimodal models can recognize objects, reason about unfamiliar instructions, inspect failures, and choose sensible subgoals. Their inference and network delay are slow relative to physical feedback. [Robot-Use Agents](https://web.mit.edu/phillipi/www/writing/robot-use-agents.html) describes this mismatch directly. A model may need seconds for one decision while the robot needs new control commands tens or hundreds of times per second.

The broader question is what a slow model should communicate to a robot harness: command semantics, execution boundaries, observation requests, and evidence for another model turn. The answer could depend on the task and available sensors. A phased feedback command is one conjecture, not an established choice.

No public source gives a stable 0.6–0.8 Hz rate for Astra, and OpenAI publishes no robot-control latency guarantee. The experiments should log observed latency and evaluate a range of model-call intervals.

## How Astra is currently connected to robots

### RoboCurve and Inspect Robots

[RoboCurve's Astra evaluation](https://openai.robocurve.org/gpt-6-astra/) gives the model three camera views, proprioception, and a small robot API. Astra returns absolute end-effector position, orientation, and gripper commands. Inverse kinematics and safety checks convert those targets to robot motion. The model receives another observation after the motion segment.

The reported result is 19/20 on block-into-bowl and 2/20 on puzzle insertion. This establishes that direct Cartesian control can expose real spatial competence. Each new semantic or geometric correction still requires another model turn.

[Inspect Robots](https://github.com/robocurve/inspect-robots) is useful evaluation infrastructure because it records agent and robot traces behind a common interface. It does not settle which action representation a frontier model should use.

[LIBERO-Agent](https://arxiv.org/html/2609.39507) evaluates general-purpose agents issuing bounded native end-effector actions in a LIBERO-based simulator. Astra completed its easy single-object pick-and-place task in 3/3 reported rollouts, while the paper reports lower success on harder short-horizon tasks and lower stable stage completion on long-horizon tasks. These are different tasks and an agent-selected observation protocol, so they do not predict performance on a particular standard LIBERO task under our medium-effort policy setup. They do caution against treating a simple pick-and-place task as an assured failure case.

### GPT-6 Astra as an Embodied Policy

The public technical report [GPT-6 Astra as an Embodied Policy](https://anonymous-report-421.github.io/public-website/?lang=en&view=1) evaluates direct Astra and a π0.5+Astra hybrid on ten RoboDojo tasks. The report lists Jiayi Su, Yixin Zheng, Mi Yan, Li Yi, Zhizheng Zhang, and Wang He as authors, although the hosting account is anonymous.

Its direct system gives Astra three RGB views, proprioception, measured end-effector poses, and bounded end-effector actions. Each direct action contains one to five 25 Hz control steps. The hybrid asks a RoboDojo-finetuned π0.5 policy for fifty candidate steps, then lets Astra accept up to fifteen steps or replace a short segment with bounded end-effector corrections.

The report gives 26% success for direct Astra and 48% for the hybrid over fifty RoboDojo cases. It also reports 98% direct Astra success on a selected RoboLab subset dominated by semantic pick-and-place. These numbers should not be mixed. The RoboLab runs used different tasks and some unmatched conditions.

The released [GPT-as-Policy repository](https://github.com/anonymous-report-421/GPT-as-Policy) contains controller, rollout, scheduler, results, and report code. It is a history-free one-commit export and requires separately installed RoboDojo assets, Isaac Sim, checkpoints, and model access. It omits original model sessions and raw operations logs. This is a protocol and results reference; the first experiment need not reproduce it.

### Agent as Policy and GPT-Policy

[Agent as Policy](https://agent-as-policy-2026.github.io/) gives a frontier agent documented robot tools, observations, and a writable workspace. The agent can call end-effector, joint, and gripper tools or write Python programs. The robot bridge handles IK, limits, and trajectory execution, so motion can continue without waiting for another inference. This is real prior work for programmatic, temporally extended frontier-agent control. It does not hold the downstream computation fixed or measure which communication fields account for success.

[GPT-Policy](https://github.com/cheng-haha/GPT-Policy) uses structured Cartesian targets and waypoint sequences. Its controller validates sequential IK, executes the requested motion, and returns fresh observations. This is another example of a frontier model acting through poses and short trajectories rather than direct torque control.

### Public Astra demonstrations

Public posts show Astra controlling tabletop arms, dual-arm systems, quadrupeds, keyboards, and painting setups. The [Awesome Robot-Use Agent index](https://kairunwen.github.io/Awesome-Robot-Use-Agent/) collects many of these examples and links to their original posts and repositories.

The disclosed interfaces fall into a few recurring groups:

- one pose or short Cartesian segment followed by a new observation;
- a sparse trajectory passed to an existing controller;
- high-level selection over a VLA or locomotion policy;
- model-written controller code or motion programs.

These demonstrations matter as prior art. They prevent claims that Astra has never controlled robots, emitted trajectories, or written controllers. Most do not report matched trials, failures, call timing, held-out instances, or a full executor specification. They are evidence of possible behavior, not substitutes for a controlled benchmark.

## Other frontier-agent systems

[VIA](https://arxiv.org/abs/2607.11119) gives a general software agent a visual 3D interface, a virtual gripper, and robot tools. A waypoint command is executed by an existing controller. Its results show that an unmodified agent can operate in a robot loop, while interface guidance, perception tools, task tips, and control APIs contribute together.

[Waddle](https://www.waddlelabs.ai/research/introducing-waddle) lets a general agent write programs against robotics tools for perception, kinematics, planning, and execution. It shows the reach of an agent-plus-tools system but does not isolate the message passed from agent to controller.

[Claude Plays Robotics](https://www.anthropic.com/research/claude-plays-robotics) compares several ways of connecting a general model to robots. Direct low-level commands are weak; generated controllers and pretrained policies can do better. A cursor that returns depth at a selected pixel helps more than several denser visual overlays in one reported manipulation ablation. Useful geometry may depend on how the model queries it.

These systems motivate a narrower experiment. They should not all become baselines.

The local study may test faster verified completion at comparable observed success, rather than only a success-rate increase. Calls, inference time and simulated motion time are distinct costs. Existing reports that change planning, perception and execution together motivate a controlled efficiency comparison but do not isolate a speed advantage for our proposed communication boundary.

## Programs, spatial objectives, and learned skills

[Code as Policies](https://arxiv.org/abs/2209.07753) generates programs that compose perception and robot APIs. Code can express loops, state, and conditions, but the available APIs determine much of the physical competence.

[Show-Harness](https://arxiv.org/html/2609.10522) is especially close to the broad idea of a constrained robot interface for a frontier VLM. It exposes compact semantic movement and gripper units, grounds them through embodiment-specific interpreters, and adds observation, planning, action history, and recovery plugins. It already conducts a partial recipe-style analysis: removing multi-view guidance, proprioception, subtask planning, action history, or failure recovery hurts in its tested settings; always-on action chunking reduces success, while selective chunking saves calls; visual prompting and situated planning help particular scenarios. Its action-name/convention ablation finds explicit physical conventions more important than semantic names alone. These are findings for its chosen model, tasks, and interface, not universal necessities. Our work cannot claim that a compact, interpretable harness or component ablations are new. Its action units are incremental decisions returned to the model after each step; a model-specified, bounded command with sensor-measurable exits would be a different delegation boundary, but that difference needs a matched empirical test rather than a novelty assertion.

[RPent / Harness VLA](https://rpent.readthedocs.io/en/latest/rst_source/resources/harnessvla.html) offers fixed analytic robot primitives and frozen VLA skills for an agent to compose. [PyRUA-Lean](https://arxiv.org/html/2610.01939) lets Astra write Python cells that conditionally compose those same primitives and choose which observations return. Against RPent tool calling on 700 paired simulated instances, it reports 63.1% versus 71.7% success, while changing code composition, persistent state, and observation delivery together. This is close prior work for a harness study: our contribution cannot be the generic claim that feedback, conditional execution, or primitive composition helps. Its reported gain does not isolate which of those interface features caused it.

[CaP-X](https://github.com/capgym/cap-x) extends this direction with feedback and replanning around generated programs. Its loops are relevant to slow frontier agents, but code can call arbitrary support functions. A comparison with constrained commands would need to account for the different tools available to generated code.

[VoxPoser](https://voxposer.github.io/) builds 3D value maps from language and optimizes robot motion against them. It demonstrates the value of spatial objectives and the associated confound: perception, affordance models, and optimization can supply substantial downstream intelligence.

[SayCan](https://say-can.github.io/) combines language-model scores with learned affordances over a fixed skill set. Its skill policies already contain robot behavior. This is a different delegation boundary from a generic controller executing model-specified feedback errors.

[RT-Trajectory](https://arxiv.org/abs/2311.01977), [Any-point Trajectory Modeling](https://arxiv.org/abs/2401.00025), [RoboPoint](https://robopoint.github.io/), and [OmniManip](https://arxiv.org/abs/2501.03841) show the usefulness of trajectory sketches, point tracks, affordance points, and object-centric interaction geometry. Their models learn from robot or spatial supervision. They support these representations as candidates without answering whether Astra can specify them accurately with its weights fixed.

## What tracking and visual servoing can supply

[Visual servoing](https://web.mit.edu/amcp/OldFiles/drg/Chaumette_Part_I.pdf) repeatedly measures image error and moves the robot to reduce it. [Operational-space control](https://khatib.stanford.edu/publications/pdfs/Khatib_1987_RA.pdf) controls end-effector motion and force instead of joint commands. [Impedance control](https://summerschool.stiff-project.org/fileadmin/pdf/Hog1985.pdf) regulates the robot's response during contact. These methods provide fast feedback; they do not select the task, object, grasp, or phase sequence.

Model predictive control can replan a motion from current state while enforcing dynamics and constraints. It still needs a cost that reflects the task and a state estimate that remains valid. Giving one interface a rich planner while another receives only IK would confound a comparison. The first experiment should use the same underlying motion controller for each condition.

[TAPIR](https://deepmind-tapir.github.io/) and [CoTracker3](https://cotracker3.github.io/) provide online point tracking. [RoboTAP](https://deepmind.google/research/publications/38759/) uses tracked points as a bottleneck for few-shot imitation and completes real manipulation tasks from demonstrations. This is strong evidence that local point correspondence can support control.

It is not evidence that generic tracking solves open-world manipulation. CoTracker3 reports failures on featureless surfaces. Trackers can drift, remain confidently wrong through occlusion, or lose the relevant surface when an object rotates. A point track also does not reveal grasp success, force, stable support, or task completion.

Tracking is a possible measurement source when visible correspondence defines the relevant error. It should be tested before it is placed inside an executor. Robot state, depth, gripper state, or contact signals may suit other phases if the chosen simulator and later hardware expose them.

## Temporal abstraction and exits

The [options framework](https://people.eecs.berkeley.edu/~russell/classes/cs294/f05/papers/sutton%2Bal-1999.pdf) formalizes actions that run over multiple time steps and terminate under stated conditions. [Behavior trees](https://doi.org/10.1109/TRO.2016.2633567) make running, success, and failure explicit.

Both ideas fit the rate problem. A slow model can specify several phases and let a fast executor advance when sensor conditions pass. They also create a risk: a library of task-specific options or behavior-tree leaves can solve the benchmark independently of Astra.

Direct-control pilots should determine which command semantics, feedback, and observation handoff are worth testing before adding multi-phase execution.

## Robot-trained policies as external references

[RT-X](https://arxiv.org/abs/2310.08864), [Octo](https://arxiv.org/abs/2405.12213), [OpenVLA](https://arxiv.org/abs/2406.09246), and [π0](https://www.physicalintelligence.company/download/pi0.pdf) learn action distributions from robot datasets. Their success measures what robot-specific training can provide: motor priors, action chunks, contact experience, and recovery patterns.

They are valuable references for what robot-specific training provides, but their scores should not be treated as matched baselines for an interface experiment using a general foundation model.

## What prior work already occupies

Prior work has shown that:

- frontier agents can control robots through poses, trajectories, tools, and generated programs;
- compact semantic action interfaces can connect frontier VLMs to robots;
- low-level motion can continue while a frontier model reasons;
- VLA proposals can be combined with frontier-model review;
- visual tracks and spatial objectives can guide manipulation;
- task-trained policies provide motor knowledge that general models may lack.

The project should not claim any of these as new.

## Relation to the local experiment

The local LIBERO setup renders and replays fixed native-action episodes. Astra at medium effort achieved native task success on the microwave pilot and recovered from empty grasps and blocked insertion. The user requested a different task rather than another microwave pilot. The initial-state settling issue is a protocol observation, not evidence about the cited systems or a communication-harness gain. That pilot alone established no paired result or revised theoretical claim. Current implementation details and exclusions are recorded in [sensor_audit.md](sensor_audit.md).

For task screening, RoboCurve's puzzle result and one raw stage-3 transcript were rechecked on 2026-10-06. The official RoboDojo precision-task source and LIBERO-PRO perturbation configuration were also inspected. These sources motivate testing a native MuJoCo insertion analogue; their published failure rates do not transfer automatically to this setup. Other claims in this provisional review remain to be rechecked.

The two native ToolHang pilots yielded one full success and one budget-limited failure after frame assembly, both replaying exactly. Their grasp, insertion and withdrawal errors are local evidence; they do not reproduce RoboCurve's failure rate. Repeated non-arrival before later phases and blocked motion support selecting a measured transition/handoff experiment. Failure at final tool placement despite near-arrival limits the proposed mechanism. No mechanism benefit has been measured.

## Current empirical boundary

The completed local ToolHang comparison achieved 0/2 full native successes in each of timed, deadline and early-arrival control. The first baseline left the correct hole shallowly suspended; the first deadline hung the tool but never assembled the frame; the first early-arrival run lost completed assembly during wrist recovery. Second-start failures included shallow/outside frame placement, unthreaded tool placement and the last baseline's suspension via the smaller hole. The [empirical account](empirical_account.md) distinguishes partial physical progress, native geometry and policy judgments. Resource reductions in failed episodes do not establish faster completion.

The installed scorer matches official robosuite v1.4.1, and a saved-state audit reproduces positive pilot and intermediate subchecks as well as all final outcomes. No scorer/wrapper mismatch was found. Two matched starts are not six independent placements, and their wide uncertainty precludes reliability or generalization claims. Service interruptions and one simulator reconstruction are retained rather than substituted with fresh episodes.

These findings revise the local H3 conjecture: robot-pose exits do not verify model-intended object relations or whole-arm clearance. They motivate testing the measurement feasibility of model-selected public RGB-D anchors before a feedback mechanism is built. Tracking and visual-servoing prior art supports considering that route, not assuming it works here; wrong identities and hidden geometry remain separate limits. The [next-test decision](../studies/object_feedback_feasibility/decision.md) is development using observed traces, not held-out evidence. Other external claims in this provisional review still need source verification before final submission.

The inference was clarified after the user challenged rejecting arrival gating: 0/2 in each condition supplies no observed benefit, but shared placement failures can mask a guard effect. The broader effect remains unresolved. Re-executing both original pilot command sequences under the current timed baseline reproduces every action/state exactly and retains one success / one failure; this rules out a physical execution regression for those sequences, without equating prompts or model decisions. The proposed object-point measurement audit investigates a complementary bottleneck, not evidence that arrival gating is universally ineffective. See [the regression decision](../studies/tool_hang_v1/baseline_regression_decision.md).

The subsequent local measurement audit tested an [OpenCV pyramidal Lucas-Kanade correspondence prototype](https://docs.opencv.org/4.7.0/dc/d6b/group__video__track.html), with explicit depth, consistency and loss thresholds frozen before scoring. Its 63.1% visible coverage, 9.28 mm accepted-error p95 and 25.9% false-valid rate failed the declared gate on recorded ToolHang motions. These results concern this prototype and sensor/task geometry, not tracking methods generally. A small round-trip residual did not certify correspondence identity. The official [CoTracker3 repository](https://github.com/facebookresearch/co-tracker) and [online predictor source](https://github.com/facebookresearch/co-tracker/blob/main/cotracker/predictor.py), inspected on 2026-10-08, support considering a learned visibility estimate; they do not establish local accuracy or runtime. Its windowed output also needs an explicit causal timing account. [The next-test decision](../studies/object_feedback_learned/decision.md) checks those prerequisites before another accuracy audit or Astra experiment.

## Causal tracking runtime and next measurement test (2026-10-08)

The official scaled-online CoTracker3 probe produced causal outputs on this Mac. Combined two-camera steady-update p95 was 2.167 seconds; the original 0.4-second runtime gate failed. Sol chose that threshold from eight frames at 20 Hz. It was not a user requirement. The goal permits paused physics and slower measurement, so the runtime result does not automatically exclude a feedback executor. Preserve its failed real-time criterion and withdraw the stronger exclusion; include actual local computation in a subsequent elapsed-time comparison. See [the runtime account](../studies/object_feedback_learned/runtime_account.md).

The separately recorded [accuracy decision](../studies/object_feedback_learned/accuracy_decision.md) retains all 212 original queries, frozen tracker settings and the numerical precision/coverage/loss gates. It scores only current endpoints available after a 16-frame bootstrap and then eight new frames, plus final partial updates. A full control-frame ledger records fresh measurement unavailable between updates. This periodic interface is distinct from the failed 20 Hz local-flow screen. A passing measurement would justify a bounded sensor-driven prototype and then two new matched starts; it would not itself establish H1 or a task benefit. H1 has not yet had its robot comparison, H3's wider effect remains unresolved, and H2/H4 remain open.

The completed [causal CoTracker3 accuracy audit](../studies/object_feedback_learned/accuracy_account.md) retained 97.7% of visible endpoints but failed the unchanged precision/loss gates (5.55 mm error p95; 24.8% occluded false-valid). All 212 queries, 2,757 endpoints and 22,739 availability rows are retained; actions and queried sensors reconstructed exactly. Private overlays show that subpixel tracking near a thin surface can sample background depth and produce metre-scale world error. This rejects the tested RGB-tracker/nearest-depth measurement for precision feedback; it does not reject H1. The [next recorded test](../studies/robot_feedback_modalities/decision.md) explores robot progress, finger opening and compensated wrist loads, starting with two fixed free-motion calibration runs before any new Astra comparison.

The subsequent [robot-feedback screen](../studies/robot_feedback_modalities/account.md) verified empty-gripper load compensation on two fixed starts and screened all six original traces. Load and progress flags missed an upstream arm collision, while stable empty-sized closure exposed seven unoccupied/partial-contact waypoints. The [bounded empty-closure prototype](../studies/robot_feedback_modalities/guard_account.md) passed four predefined paired fixed fixtures: it cancelled an empty lift and allowed the successful retry, with exact action/state prefixes and sensor replay. Astra must explicitly arm this warning and choose recovery; it does not certify acquisition or seating. That development screen established no policy task benefit. The subsequently completed paired comparison is reported below.

## Completed empty-closure screen and next test (2026-10-08)

The [four scheduled v2 episodes](../studies/tool_hang_v2/account.md) finished with guarded 2/2 and timed 0/2 native successes. The first pair is prompt-confounded; only the second pair is matched. Guarded succeeded there after two correct empty-sized interrupts cancelling 105 requested steps, while timed recovered a grasp slip but declared completion with the tool contacting the wrong frame section and table. No jointly successful pair exists for an efficiency comparison. The clean guarded run used more calls and simulated time than the failed baseline. Small-sample uncertainty, interrupted host clocks and the prompt erratum preclude a general reliability or speed claim.

Retain the observed empty-continuation invalidation/handoff behavior. It does not certify acquisition or seating, and the first guarded success had no stop. Short returned command reasons are audited against public sensors and motion, with private geometry diagnosing discrepancies; they are self-reports, not complete internal reasoning or isolated causal evidence. The [current empirical account](empirical_account.md) separates all stages and outcomes.

The [selected next test](../studies/tool_hang_v2/next_test.md) broadens the question to object-relation measurement. One frozen public-depth/uncertainty screen reuses all original CoTracker predictions, with coverage, precision and loss scored together. A passing development screen permits a separately frozen H1 robot comparison on two new matched starts; a tracking-specific remaining gap permits one official TAPNext++ screen. If usable feedback does not emerge, retire that route for this iteration and choose another trace-supported representation/feasibility question. No guard retuning or extra v2 start is scheduled. The broader FYP remains active.

## Completed depth uncertainty screen (2026-10-08)

The [frozen public-depth screen](../studies/object_feedback_depth/account.md) completed on all 212 queries and 2,757 original endpoints. Local support/median reduced occluded false-valid acceptance from 24.78% to 16.52%, but visible coverage fell from 97.70% to 78.58%. Adding temporal and other-camera checks yielded 77.63% coverage and 4.89 mm accepted-error p95, with the same 16.52% false-valid rate. All unchanged gates fail. Of 56 accepted reference-occluded points, 19 had corroborating other-camera depth: agreement about the reported surface does not certify the original point's identity. Actions, states, original query sensors and the unchanged measurement control reproduce exactly. No Astra requests or new tracker forwards were used.

The proposed tracker follow-up was subsequently retired at the user's request. The [current decision](../studies/mechanism_selection/decision.md) moves to a different trace-supported communication mechanism before another policy batch. The [action-reason analysis](../studies/tool_hang_v2/reason_analysis.md) records stated expectations, observed contradictions and recovery choices; these are self-reports checked against traces, not complete internal reasoning or causal proof. Two matched starts remain the default for subsequent policy comparisons.

## Tracker step deferred; next mechanism selection (2026-10-08)

The user requested moving on and deleting the alternative tracker files. Its study records, downloaded source and checkpoint have been removed. No tracker accuracy conclusion is drawn. The completed depth results remain retained.

The [new decision](../studies/mechanism_selection/decision.md) supersedes the tracker schedule and retires tracked-surface correction for this iteration. Next select a communication/embodiment mechanism from actual rotation and placement traces: bounded rigid-motion delegation is the candidate if transform/trajectory bookkeeping contributes; feasibility or explicit relation representation takes precedence if those dominate. Inspect the recorded public calculations and action reasons before implementing it. The next substantive policy comparison still uses two new matched starts with a prospective prediction, credible waypoint baseline and identical controller/sensor/calculation budgets. No new accuracy gates or guard variations are introduced.

## Selected pose-feasibility mechanism (2026-10-08)

The [rotation discriminator](../studies/mechanism_selection/account.md) found coherent logged rigid-transform calculations, substantial pose nonarrival and a last-joint limit during one failed settling move. A fixed robot-only IK screen solved 14 of 17 predefined targets and found no tolerance-passing solution for three troublesome wrist targets. It also solved the final wrong-placement targets, so feasibility cannot certify task geometry. This is a development selection result, not global unreachability or policy efficacy. An invalid first export omitted the radians compiler setting; that attempt is retained as invalid, and the corrected screen verifies FK and compiled joint bounds against the original robot.

Select an optional structured pose-feasibility query under bounded computational delegation. Astra chooses candidate poses and any subsequent motion/recovery; the query advances no physics and neither replaces nor cancels commands. Both conditions receive genuine joint positions, the known robot model and identical calculation libraries/access. Earlier native policy inputs omitted joint angles, so this is an explicit shared sensor amendment. The [prospective protocol](../studies/mechanism_selection/mechanism_protocol.json) fixes two new matched starts and four episodes before implementation. Verify paired fixed executions and freeze source/prompt equality before spending Astra calls. The generic waypoint controller and shared empty-closure semantics remain common. No tracker development resumes.
