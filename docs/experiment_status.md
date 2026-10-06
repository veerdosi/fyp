# Experiment status

The objective is a paired comparison guided by direct-control failures. Simulator setup is in progress. No Astra episode has run, no evaluation task has been selected, and no harness hypothesis has been evaluated.

The original three research documents are provisional. Their linked literature claims have not yet been rechecked during this experiment.

The main agent owns implementation and analysis. Every robot-policy episode must use a fresh GPT-6 Astra context with medium reasoning effort. Astra may select actions and sensing queries; it may not delegate or assist with project development.

## Evidence gates

1. Reproduce a fixed-sequence LIBERO episode and audit sensors.
2. Run a few direct-control pilots and diagnose their first causal failure.
3. Record task selection and predictions before implementing a harness.
4. Freeze paired conditions and held-out starts before evaluation.
5. Report outcomes, uncertainty, resources, failures, and a revised explanation.

Git milestone `0998edb` records the provisional starting documents. The first target is the standard LIBERO-10 yellow-and-white mug / microwave task specified in the goal file.
