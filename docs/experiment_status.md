# Experiment status

The objective is a paired comparison guided by direct-control failures. The fresh LIBERO setup is runnable. Two fixed-sequence runs replayed exactly (40 and 60 control steps). The first Astra microwave pilot achieved native success; the second was aborted at the user’s request. No evaluation task has been selected, and no harness hypothesis has been evaluated.

The first pilot began without initial settling. Astra measured the target mug before it dropped about 6 cm; its first grasp closed above it. It then detected empty grasps, changed to a handle grasp, lifted and transported the mug, and encountered blocked insertion at the microwave entrance. Astra recovered and satisfied the task at step 1581. These are exploratory pilot observations, not held-out findings. Later episodes begin with a fixed 20-step settling period. The settled verification run also replayed with maximum state error 0.0.

Agent session records verify GPT-6 Astra at medium effort and expose per-request token usage. The report will distinguish policy decisions from actual model inference requests, and standard API-equivalent cost from unknown actual account charges. Policy reasoning text is not exported.

The original three research documents are provisional. Their linked literature claims have not yet been rechecked during this experiment.

The main agent owns implementation and analysis. Every robot-policy episode must use a fresh GPT-6 Astra context with medium reasoning effort. Astra may select actions and sensing queries and run logged temporary calculations from permitted sensors; it may not delegate or assist with project development. The updated routing skill was validated.

## Evidence gates

1. Reproduce a fixed-sequence LIBERO episode and audit sensors.
2. Run a few direct-control pilots and diagnose their first causal failure.
3. Record task selection and predictions before implementing a harness.
4. Freeze paired conditions and held-out starts before evaluation.
5. Report outcomes, uncertainty, resources, failures, and a revised explanation.

Git milestone `0998edb` records the provisional starting documents. The first target is the standard LIBERO-10 yellow-and-white mug / microwave task specified in the goal file.

The microwave task is retired from further screening at the user’s request. No stacking episode was launched; that proposal was rejected. The drawer candidate was also stopped at the user’s request after Astra opened it on its first pull. Existing native MuJoCo insertion scenes were then audited; ToolHang is the preferred next screening candidate. Two 60-step native-task smoke traces replayed exactly. There is no evaluation freeze or harness implementation yet. See [task_screening.md](task_screening.md).
