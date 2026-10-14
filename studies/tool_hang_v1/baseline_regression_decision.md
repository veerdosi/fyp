# Pilot-to-held-out baseline audit

Recorded 2026-10-08 before command re-execution, following the user's question about 1/2 pilot successes versus 0/2 held-out baseline successes.

The six overall failures do not reject a population benefit of arrival gating. Three conditions share only two starts. Native full success can have a floor when common object-placement failures dominate; guards can affect execution without converting either sampled episode to full success. Keep the observed primary null result and all scheduled outcomes. Replace the claim that this screen falsifies arrival gating with: **no demonstrated benefit; insufficient for these starts; wider benefit unresolved**.

Next check: execute the exact recorded commands from both ToolHang pilots using the current timed baseline, at their original seed/state and limits. No Astra inference, replanning, target repair, different duration or scoring changes. These two diagnostic starts are existing pilot data, not extra held-out trials. Retain both outcomes, complete native actions/states and source/config records. Compare actions and states with each original trajectory and replay the verification traces.

Prediction if the baseline's physical execution is unchanged: actions/states match within the existing replay tolerance (1e-7), with the original success for pilot 001 and original budget failure for pilot 002. A mismatch requires diagnosing the regression before interpreting the held-out performance change or launching another mechanism study.

Source/config audit already shows matched controller, sensors, budgets, medium model effort and initial settling. The first pilot's task instruction said "by its hole"; it was clarified to "larger hole" before pilot 002. Guard implementation adds execution reports to timed control, so policy feedback is not identical to the pilots. Command re-execution tests physical execution, not equality of model behavior under those prompts. Two pilot observations cannot establish a stable 50% success probability. Different held-out placements and policy decisions remain explanations to inspect, not statistically identified causes.

Pause implementation of the proposed object-point feasibility prototype until this regression check and interpretation are resolved. Its recorded decision remains a candidate next measurement test, not a justification for discarding arrival gating. Further tests must isolate the uncertainty that matters, retain the two-start default and avoid positive-result chasing.

Cleanup, 2026-10-14: the redundant generated `verify_pilot_commands_*` folders were removed. The original pilot traces and [regression comparison report](verification_summary.json) remain. The driver can regenerate the check; frozen historical source paths require the recorded revision.
