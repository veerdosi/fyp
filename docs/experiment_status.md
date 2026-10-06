# Experiment status

The objective is a paired comparison guided by direct-control traces, including opportunities for success, calls, time or cost improvements. The fresh LIBERO setup is runnable. Two fixed-sequence runs replayed exactly (40 and 60 control steps). The first Astra microwave pilot achieved native success; the second was aborted at the user's request. The first native ToolHang policy pilot also succeeded and replayed exactly. No evaluation task has been selected, and no harness hypothesis has been evaluated.

The first pilot began without initial settling. Astra measured the target mug before it dropped about 6 cm; its first grasp closed above it. It then detected empty grasps, changed to a handle grasp, lifted and transported the mug, and encountered blocked insertion at the microwave entrance. Astra recovered and satisfied the task at step 1581. These are exploratory pilot observations, not held-out findings. Later episodes begin with a fixed 20-step settling period. The settled verification run also replayed with maximum state error 0.0.

Agent session records verify GPT-6 Astra at medium effort and expose per-request token usage. The report will distinguish policy decisions from actual model inference requests, and standard API-equivalent cost from unknown actual account charges. Policy reasoning text is not exported.

The original three research documents are provisional. RoboCurve's puzzle results and one raw transcript, official RoboDojo precision-task code, LIBERO-PRO configuration, Show-Harness and PyRUA-Lean were rechecked for the current screening questions. Other linked claims remain provisional.

The main agent owns implementation and analysis. Every robot-policy episode must use a fresh GPT-6 Astra context with medium reasoning effort. Astra may select actions and sensing queries and run logged temporary calculations from permitted sensors; it may not delegate or assist with project development. The updated routing skill was validated.

## Evidence gates

1. Reproduce a fixed-sequence LIBERO episode and audit sensors.
2. Run a few direct-control pilots and diagnose their first causal failure.
3. Record task selection and predictions before implementing a harness.
4. Freeze paired conditions and held-out starts before evaluation.
5. Report outcomes, uncertainty, resources, failures, and a revised explanation.

Git milestone `0998edb` records the provisional starting documents. The first target is the standard LIBERO-10 yellow-and-white mug / microwave task specified in the goal file.

The microwave task is retired from further screening at the user's request. No stacking episode was launched; that proposal was rejected. Existing native MuJoCo insertion scenes were then audited. Two 60-step native-task smoke traces replayed exactly.

ToolHang pilot 001 completed both assembly steps and correctly returned `finish`, using 20 robot decisions, 40 actual inference requests, 92.75 simulated seconds and 353.274 seconds of policy time. Its 1855 native actions replay exactly. Empty grasps, blocked insertion and a snagged withdrawal were recovered by Astra. Non-arrival before a subsequent gripper phase supplies a specific command-transition question; it does not establish a harness benefit. A second initial state is needed for screening repeatability before selecting the task and mechanism. There is no evaluation freeze or harness implementation yet. See [task_screening.md](task_screening.md) and [the trace analysis](pilot_tool_hang_trace.md).
