# Research plan

Current decision: 2026-10-14. The [original objective](goal_objective.md) remains
the project scope; [the results account](empirical_account.md) is the record of
completed findings. This file contains the current plan, not a running chronology.

## Research question

Which information and action interface lets a foundation model control a robot
more effectively, and which observed limitation explains the effect? Improvements
may concern verified success, calls, time or cost. A positive effect is not assumed.

The latest [cross-episode audit](../studies/cross_episode_failure_audit/account.md)
reviewed 394 returned reasons in 16 ToolHang episodes. Clear grasp contradictions
often prompt recovery; placement, release and verification remain less reliable.
These are behavioral observations, not access to hidden reasoning or evidence of
an intrinsic limitation across tasks. See the account for counts and counterexamples.

## Next decision

Switch evaluation tasks and select a controlled diagnostic before another harness
prototype. Distinguish incorrect feature/geometry estimates, incorrect conversion
of object intent into robot commands, physical execution constraints and unsupported
completion judgments. A new task has not yet been frozen. Require asymmetric visible features, an explicit
observable goal, useful policy progress and a controlled change that does not
accidentally make physical reachability or millimetre-scale contact the main confound.

| Diagnostic change | Expected consistency | Question raised by a discrepancy |
| --- | --- | --- |
| Camera viewpoint, physical state unchanged | Same selected physical feature and desired world-frame placement | Grounding/reference frames, after checking visibility |
| Held-object orientation or grasp offset | Same object-to-target goal, appropriately changed gripper motion | Conversion into actions, after checking attachment |
| Visibility of support/engagement evidence | Same physical outcome; confidence/sensing respond to evidence | Verification/observability, after checking score ambiguity |

Choose one axis before running it, with a prospective short-episode protocol. Every
Astra diagnostic still belongs to an actual robot episode and selects executable
actions or sensing; no advisor calls or detached reasoning quizzes. Record selected
features, public geometry estimates, requested/achieved motion and predicted outcome
in the same manner across conditions. These diagnostic outputs can affect behavior;
do not equate the new prompt with historical direct-control prompts.

Object-relation representation is a candidate intervention, not the selected answer.
Collision checking and contact correction are not the main next study. The previously
recorded zero-Astra wrist screen remains a possible prerequisite if contact handling
becomes the supported question. Tracker development and further stopping variants
are not scheduled. A failed estimator does not reject every feedback mechanism.

## Design rules

Use two matched starting states per experiment. Add a third only to resolve a
specific decision-changing uncertainty, recorded before launch. Do not replace
failures or expand counts after inspecting outcomes. Each policy episode uses a
fresh Astra medium context and the same permitted calculation access.

Before evaluation, state the prediction, primary measure and failure criterion;
freeze task, conditions, starts, budgets, controller, sensors and executor code.
Keep a credible direct pose/waypoint baseline with fresh observations and replanning.
Separate changed information from changed action representation or stronger control.
Use pilots for selection, then new starts for the mechanism comparison. Label any
staged checkpoint or deliberate disturbance as a diagnostic intervention.

Measure intended geometry, requested motion, achieved motion and post-action
relations separately. Keep ambiguous/mixed explanations explicit. Native object
state, contacts and success are scoring/diagnosis only. Astra chooses the task
features, grasps, goals, sensing, recovery and completion; Sol supplies the declared
measurement/control responsibilities. See [the interface](communication_interface.md).

Report every scheduled success/failure, first meaningful failure, decisions, actual
inference requests, simulated motion, native policy time, execution/delivery/host
clocks, tokens and API-equivalent cost. Failed runs cannot establish faster completion;
resource ratios require jointly successful pairs. Small samples do not establish
population reliability, equivalence or cross-task generality. Interrupted host clocks
cannot support an elapsed-speed claim.

## Starting hypotheses and current evidence

| Starting hypothesis | What has been established |
| --- | --- |
| H1: correction during motion | Not tested in a paired robot comparison; the tested point/depth prerequisites failed |
| H2: temporal extension | Not isolated from other interface differences |
| H3: measurable exits | Arrival guards showed no task benefit here; narrow empty-closure invalidation is retained, with one clean comparison pair |
| H4: bounded delegation | Optional endpoint IK query showed no contribution on two starts; its warning pathway was not engaged |

These are starting conjectures, not a four-feature implementation checklist. Retain,
revise or reject a mechanism based on what its comparison actually tested. Generality
requires a frozen interface tested on a suitable changed task/object, not task-specific
executor additions. The next study should discriminate explanations before optimizing
another part of the current pipeline.

## Deliverable

Runnable code, replayable evidence, an interpretable paired comparison and a concise
empirical/conceptual account for the supervisor. Completing a small batch is one stage,
not the entire FYP. Follow [AGENTS.md](../AGENTS.md) for durable experiment rules and
[the literature review](literature_review.md) before making novelty claims.
