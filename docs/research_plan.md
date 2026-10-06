# Working research plan: a constrained robot-control harness

**Status:** working plan, not a fixed interface or paper claim. Read [communication_interface.md](communication_interface.md) for the initial design conjecture and [literature_review.md](literature_review.md) for prior work.

## Research question

Can a constrained model-to-robot harness improve task success or efficiency over direct control? Which choices about commands, executor behavior, observations, and handoff between model turns account for any difference, and under what conditions?

The starting conjecture is that a model could specify a measurable objective, bounded execution, and observable success or abort conditions for a controller to execute. The four items in the original slide are **research hypotheses about the harness**, each with a paired test and failure criterion. They are not four sequential robot actions or a fixed implementation recipe. The research path is to state what the conjecture predicts, inspect actual failures, test a small harness against strong alternatives, and revise the explanation from the results.

| Candidate hypothesis   | Diagnostic comparison                                                                                               | What would count against it                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| H1: Feedback closure   | Execute the same accepted Astra command with live feedback and with fixed execution                                 | Live feedback does not improve recovery from a disturbance            |
| H2: Temporal extension | Compare progress and success per model call under longer gaps against direct pose **and credible waypoint** control | Direct control matches the extended condition at the same call budget |
| H3: Measurable exits   | Remove completion and invalidation checks while keeping the rest of the executor fixed                              | Checks do not reduce stale execution or inappropriate stopping        |
| H4: Bounded delegation | Freeze the executor and command vocabulary before testing held-out tasks                                            | New per-task executor, grasp, or recovery rules are needed to succeed |

These are proposed tests, not promised results or four mandatory features. Pilot failures may justify revising or rejecting one, or adding a new hypothesis outside H1-H4. State the predicted effect, paired test, and failure criterion for each hypothesis selected for main evaluation. Keep pilot-generated ideas distinct from results on held-out runs. Safety limits stay active in every condition, including the H3 ablation.

Use GPT-6 Astra at medium reasoning effort as the robot policy during episodes because there is public evidence of useful visuospatial robot behaviour. Use Sol for development and analysis, following the `robot-policy-model-routing` skill. The hoped-for result concerns the **harness**, not a claim that Astra has a unique internal capability. A second model becomes useful after the first comparison is interpretable.

The core comparison keeps the robot, task, raw sensor access, safety limits, model settings, and underlying motion controller fixed. The harness may change command semantics, within-command execution, observation delivery, or handoff timing. Log each difference and use ablations to identify what caused a gain; do not attribute the whole-system result to one field.

## What prior work leaves open

[PyRUA-Lean](https://arxiv.org/html/2610.01939) already studies Astra composing robot primitives with Python, and [Show-Harness](https://arxiv.org/html/2609.10522) tests a compact action interface with observation and recovery components. [VoxPoser](https://voxposer.github.io/) already uses spatial objectives and closed-loop replanning. The [literature review](literature_review.md) maps these systems and their reported results. This study must isolate a specific harness behavior or tradeoff that those results leave unresolved, then test which failures it changes and which require better perception, contact control, or task-trained policies.

## Simulator choice

Start directly with [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO), a language-conditioned manipulation task set built on robosuite/MuJoCo. The user has run LIBERO tasks on this Mac before, although that setup is gone. Install a fresh environment and start with the `libero_10` task `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it`, listed in the [official task map](https://github.com/Lifelong-Robot-Learning/LIBERO/blob/master/libero/libero/benchmark/libero_suite_task_map.py). Its success condition requires both the mug inside the microwave and the door closed. This creates observable grasp, constrained placement, and final-state checks. It is an initial task-selection hypothesis, not evidence that Astra fails this specific task or that a harness can fix its failures. [RoboCurve's Astra evaluation](https://openai.robocurve.org/gpt-6-astra/) found broad bowl placement much easier than puzzle insertion; the microwave task is a more informative candidate than repeated broad basket placement, although it is not an insertion benchmark. Use [robosuite](https://robosuite.ai/docs/installation.html) Panda `PickPlaceCan` or `Stack` only if a concrete blocker prevents the LIBERO experiment from progressing, and record the reason.

Choose the main tasks from observed failure modes, not benchmark size. Each should permit both direct control and the candidate harness under matched sensing and controller conditions, have measurable success and recoverable failures, and avoid near-certain success or failure. [LIBERO-PRO](https://github.com/hongyuxiyohung/LIBERO-PRO) can later test controlled changes in appearance, position, language, or task. Its preset perturbations chiefly probe generalization across starts and instructions; they are not automatically tests of within-episode feedback or recovery. Distinguish those questions in the results.

Do not make the first experiment depend on [RoboDojo](https://github.com/RoboDojo-Benchmark/RoboDojo) or Isaac Sim. RoboDojo has challenging precision, memory, and long-horizon tasks, but its Isaac Sim backend does not fit the local Mac setup. [RoboDojo's guide](https://robodojo-benchmark.com/doc/usage/install-and-download/) recommends an Ubuntu/NVIDIA workstation with at least 32 GB RAM and 16 GB VRAM. [Isaac Sim's requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html) exclude A100 and H100 GPUs because they lack RT cores; an NSCC allocation may therefore be unsuitable. Revisit RoboDojo as later external validation if suitable hardware is available.

MuJoCo advances only when our process steps it. Early tests can pause physics during model calls if that is recorded honestly. To study response latency, run the simulator loop independently so it keeps stepping while the model request is in flight. Do not call paused-simulation performance real-time performance.

## First runnable milestone

The default `python3` on this Mac is 3.14. The fresh `.venv` uses Python 3.11.4, robosuite 1.4.1 and MuJoCo 3.2.7. The first fixed-sequence episode rendered the requested LIBERO task and reproduced all 40 saved simulator states exactly. See [sensor_audit.md](sensor_audit.md) and `runs/smoke_001/replay_verification.json`. Policy training and CUDA packages are outside this experiment.

The first direct-control pilot succeeded: both native benchmark conditions were first satisfied at step 1581, after model-selected recovery from empty grasps and blocked insertion. The operator stopped it at step 1915 when the user requested a different task. Astra had not yet returned its completion judgment. Its initial measurement preceded an approximately 6 cm mug drop as the benchmark state settled; later pilots use a fixed 20-step settling period before policy observation. The second microwave pilot was aborted at the user’s request and is not a scored failure. This establishes a successful demo, not a reliable success rate or harness benefit. Task screening and paired evaluation remain open; see [task_screening.md](task_screening.md).

1. Run LIBERO's minimal task example without a model on `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it`: load a fixed initial state, render policy-visible camera views, step the environment, and record the task outcome.
2. Run one episode with a fixed, non-model action sequence. Save camera frames or a short video and a timestamped log of action, robot pose, gripper state, and task outcome.
3. List the observations the agent would actually receive. Check depth, contact, force, and object pose rather than assuming they are available. Keep simulator-only object pose and reward for diagnosis and scoring, but out of model and executor inputs in the main condition.
4. Confirm that the same low-level controller can execute a single pose request, a short model-specified waypoint sequence, and a continuously updated target. Resolve any mismatch before comparing methods.

This milestone is complete when one episode can be replayed and every command can be matched to the observation that produced it. A benchmark score is not required yet.

## From conjecture to diagnostic pilots

State what the candidate harness predicts before testing it, including a condition where it should offer little advantage. Use the first Astra runs to inspect failures, not prove the hypothesis. Try a small set of initial states and record the **first causal break** in each attempt: object selection, approach geometry, grasp, transport, placement, completion judgment, or controller execution. A later symptom should not hide an earlier cause.

Choose a LIBERO task variant with room to improve. A task Astra nearly always solves has a ceiling; one it cannot begin has a floor. For one controlled variant, consider moving the target object or receptacle **during** a motion segment. This tests whether a command tied to current observations differs from a stale pose. Then investigate acquisition or placement verification, where observability is harder.

Report the undisturbed task too. If a disturbance is artificial, state exactly what it isolates rather than presenting it as natural manipulation.

## Build and compare a small harness

Use pilot traces to choose the smallest testable harness addressing the [interface questions](communication_interface.md). Specify its command schema and observation handoff after inspecting failures. The executor must not hide task-specific policy decisions.

Compare on matched starts:

1. **Direct control with replanning:** after each completed motion, Astra receives fresh observations and may issue another end-effector target or a short waypoint sequence with gripper commands. Evaluate both forms if the selected task makes waypoints a credible stronger alternative; do not call a single-pose baseline representative of all direct control.
2. **Candidate harness:** Astra issues the constrained command selected from the pilot evidence; the executor performs only the declared generic mechanics and returns the specified outcomes.
3. **Mechanism controls:** when relevant, use a fixed segment or remove individual harness features to test whether execution duration, correction, exits, or observation delivery caused the result.

Keep the same robot controller, motion bounds, raw sensor access, model settings, and call accounting. A condition that needs unavailable information must be rejected and counted; simulator truth may only score or diagnose the main runs. If the harness exposes different processed observations, measure that as an interface change rather than claiming only the command changed.

Initialize Git and commit meaningful milestones. For every run, record the code revision, task, seed, condition, policy-visible input, model response, validation failure, low-level command, sensor measurement used by the executor, stop reason, task outcome, wall time, simulated time, and API cost. Inspect pilot traces and videos, then freeze the interface, baselines, success criteria, trial count, and evaluation conditions before paired runs on held-out initial states. Report success counts and uncertainty intervals as well as failure types, model calls, time, and cost.

## Revise the explanation after evaluation

- If the harness wins only when the target moves, investigate generality beyond that disturbance and compare with existing object-relative or replanning methods.
- If it wins through success or abort conditions, remove those conditions one at a time to see which caused the gain.
- If simulator truth rescues it but available sensors do not, the limit is observability. Do not present the oracle result as the deployed method.
- If fixed segments perform equally well, temporal extension may explain the gain without feedback.
- If none helps, inspect whether the model chose the wrong objective or the controller could not realize it before adding interface features.

The final research account should return to the initial conjecture: retain supported mechanisms, remove unsupported ones, and state which failure conditions each interface fits, including counterexamples. A second foundation model, more tasks, or physical hardware may strengthen a later validation; none is needed merely to chase a positive result.
