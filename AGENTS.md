# FYP experiment instructions

Sol owns research, experiment design, repository code, verification, analysis and reporting. Follow the `robot-policy-model-routing` skill: GPT-6 Astra at medium effort is used only for actual robot-policy episodes, with fresh contexts, logged inputs/outputs and no delegation. Astra owns its permitted temporary in-episode sensor calculations and robot decisions.

The user's experiment-budget preference, recorded on 2026-10-07, is **two matched starting states per experiment**. Use a third only when it is genuinely necessary to resolve a specific uncertainty that affects the next design decision. Record that reason before launching it. Do not default to larger trial counts: Astra calls are costly and the user prioritizes faster theory-to-experiment iteration.

Keep conditions matched and predefined, retain every scheduled outcome, and state the uncertainty from small samples. Resource reductions are not evidence of faster completion when a condition fails. Preserve original protocols and record user-requested count changes; do not silently change counts after inspecting outcomes.

An initial mechanism comparison is one stage of the broader FYP. Use evidence to retain, revise or discard hypotheses, then record the next necessary test before implementing it. Do not equate completing a small batch with completing the whole project.

Before a policy batch, exercise any newly allowed calculation library/helper through the actual permitted logging wrapper in both conditions using saved public-sensor fixtures. An import in the development process alone does not verify policy computation availability. Preserve and report runtime faults and mixed-protocol episodes.
