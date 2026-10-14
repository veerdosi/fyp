# Literature review

This review keeps the work relevant to the current research question. The
[research plan](research_plan.md) and [empirical account](empirical_account.md)
separate proposed explanations from local evidence. A harness or relational action
interface alone is not a novelty claim.

## Closest interface work

[Show-Harness](https://arxiv.org/html/2609.10522) connects semantic movement/gripper
units to embodiment-specific interpreters and adds observation, planning and recovery
support. It includes plugin and action-representation ablations. Our contribution
cannot simply be that a compact semantic interface helps. A new experiment needs a
specific comparison that separates information, representation and execution.

[PyRUA-Lean](https://arxiv.org/html/2610.01939) compares code composition with tool
calling using the same Astra planner and underlying primitives over 700 paired
instances. It reports 63.1% versus 71.7% success, with resource comparisons on jointly
solved instances. Code composition, persistent state and observation selection change
together; these are relevant alternatives, not isolated evidence for our proposed
mechanism. The system includes existing analytic primitives and VLA policies.

[Code as Policies](https://arxiv.org/abs/2209.07753) generates programs over perception
outputs and robot control APIs, including feedback loops. Its available support APIs
are part of the physical competence. Logged in-episode code in our baseline is
therefore important: a harness must be compared with a credible computational baseline.

[ReKep](https://rekep-robot.github.io/) generates relational keypoint constraints and
optimizes movements. [VoxPoser](https://voxposer.github.io/) uses language-derived 3D
value maps for motion synthesis. Both are precedents for spatial objectives, rather
than proof that any proposed relation command is novel or that Astra estimates it
correctly. The official [ReKep demo](https://github.com/huangwl18/ReKep) substitutes
simulator access for parts of perception; importing that demo unchanged would violate
this project's public-sensor boundary.

## Diagnosing capabilities and transfer

[RoboSpatial](https://arxiv.org/abs/2411.16537) explicitly addresses ego-, world- and
object-centric reference frames. It motivates testing consistency under controlled
viewpoint/geometry changes, but does not establish Astra's failure mechanism.

[STAR-Gen](https://arxiv.org/abs/2503.01238) distinguishes visual, semantic and
behavioral generalization. A transformed scene should isolate a declared axis;
a harder task that changes everything supplies less interpretable transfer evidence.

[ManipBench](https://manipbench.github.io/) evaluates multiple aspects of low-level
manipulation reasoning. It motivates decomposing feature interpretation, action
prediction and object interaction. Our routing restricts Astra to actual robot
episodes, so we should not silently turn this project into offline reasoning quizzes.

## What the local study can contribute

The proposed contribution is an experimentally supported explanation of when the
policy needs different observations or a different action interface, followed by a
matched test of the smallest intervention that explanation predicts. The latest
[reason audit](../studies/cross_episode_failure_audit/account.md) motivates this
question; it does not reveal hidden internal reasoning or prove a fundamental deficit.

Hold controller, sensors, computation access and budgets comparable. If an intervention
adds interpreted geometry, measure it as changed information; if it changes action
representation, avoid also adding a stronger planner. Verify observable task criteria
before treating a native-score mismatch as faulty reasoning. Record negative results
and uncertainty. Confirm novelty against the closest work once the precise diagnostic
and intervention are selected.
