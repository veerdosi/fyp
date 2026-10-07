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

The local LIBERO setup renders and replays fixed native-action episodes. Astra at medium effort achieved native task success on the microwave pilot and recovered from empty grasps and blocked insertion. The user requested a different task rather than another microwave pilot. The initial-state settling issue is a protocol observation, not evidence about the cited systems or a communication-harness gain. No paired result or revised theoretical claim has been established yet. Current implementation details and exclusions are recorded in [sensor_audit.md](sensor_audit.md).

For task screening, RoboCurve's puzzle result and one raw stage-3 transcript were rechecked on 2026-10-06. The official RoboDojo precision-task source and LIBERO-PRO perturbation configuration were also inspected. These sources motivate testing a native MuJoCo insertion analogue; their published failure rates do not transfer automatically to this setup. Other claims in this provisional review remain to be rechecked.

The two native ToolHang pilots yielded one full success and one budget-limited failure after frame assembly, both replaying exactly. Their grasp, insertion and withdrawal errors are local evidence; they do not reproduce RoboCurve's failure rate. Repeated non-arrival before later phases and blocked motion support selecting a measured transition/handoff experiment. Failure at final tool placement despite near-arrival limits the proposed mechanism. No mechanism benefit has been measured.

## Current empirical boundary

The first held-out ToolHang baseline has a recorded native failure despite physical suspension of the released tool. Arrival checks do not measure the object relation required for the frozen placement criterion. The paired comparison is incomplete, so this supplies a diagnostic boundary rather than evidence for or against a measured harness advantage. See [the interim empirical account](empirical_account.md). The pending deadline-guard run has an external Astra usage interruption, which is retained separately from manipulation outcomes.
