# Research allocation after the guard and measurement screens

The FYP evaluates communication mechanisms against observed failure types. H1–H4
are starting conjectures, not a checklist to complete or a reason to keep extending
one implementation. The user explicitly asked to broaden the research allocation
after disproportionate time on H3.

## Current choices

| Failure type | What the existing evidence shows | Experiment justified now | Limit of the claim |
| --- | --- | --- | --- |
| Incorrect geometric calculations | The four inspected public calculations reproduce exactly and use coherent rigid transforms; resulting frame corrections reach their requested orientation | Defer a rigid-motion compiler as a correctness intervention. Revisit only if a calculation error or substantial calculation overhead is measured | Correct arithmetic does not certify selected pixel identity or rigid grasp attachment |
| Sensible intent, problematic robot pose or trajectory | Three troublesome wrist targets fail a fixed bounded pose-IK screen; a changed-context recovery target passes. One settling segment reaches a joint bound | Optional structured feasibility query against credible waypoint replanning, with matched raw robot/model/calculation access | Local search failure is not global unreachability; pose feasibility is not collision or dynamic success |
| Robot arrives, object placement is wrong | Baseline final EEF targets arrive closely while the tool contacts the wrong frame section/table; a guarded release also loses the tool despite arrival | Next independent route: explicit object-relation expression and fresh evidence, if feasibility contributes little or relation errors still dominate | Must not leak native success predicates, hidden object identities or accurate simulator geometry into the policy |
| Contradicted grasp expectation | Two recorded empty continuations are correctly invalidated; one clean pair favors guarded completion, with broad uncertainty | Retain the existing narrow behavior; no further H3 variant or expanded guard batch | This does not certify grasp, repair seating, isolate a general success-rate effect or establish faster completion |
| Changing object state during a motion | The tested point/depth measurements fail precision/loss/coverage gates | Defer tracked-surface H1 correction for this iteration; no more tracker development | Failed prerequisite estimators do not falsify all live feedback or establish an H1 task result |

## Why existing feedback does not settle H1

All conditions already use ordinary robot-pose feedback in the OSC controller and
fresh observations for Astra between commands. The shared finger/load signals add
observations; the empty-closure mechanism can invalidate a continuation. Those are
distinct from the original H1 comparison: continuously adjust an ongoing declared
object-relative command from changing sensor measurements, against fixed execution
of the same accepted command. No paired robot test of that claim has been run.

There is no obligation to run one now. Its tested visual measurement route is not
usable, so defer that route and pursue a better-supported mechanism. Other live
feedback modalities can be reconsidered if a new failure warrants them. Do not call
H1 proved merely because feedback exists, or disproved because a tracker failed.

## Next experiment and decision after it

The [pose-feasibility protocol](../studies/mechanism_selection/mechanism_protocol.json)
is a planning/representation comparison, not another stopping comparison. Both
conditions use the same existing waypoint execution and explicitly armed empty
continuation behavior. The optional query changes no physics, cancels nothing and
chooses no alternative. Astra receives a bounded geometric answer and decides what
to do. Baseline calculations have the same robot data, known model and helper/library
access. The evaluated contribution is structured computational assistance.

Use the predefined two new matched starts, retain all four outcomes and measure
whether queries change unsupported target choices as well as task outcomes and
resources. A lower nonarrival count alone is a mechanism result, not a full-task or
completion-speed result. A query ignored or adding calls without a benefit is also
a useful decision: retire it for the current interface, not add another threshold
or replacement start.

If it helps, identify whether the benefit is pose choice, calls/calculation effort,
success or another prespecified resource measure. Before a generality claim, test
the same frozen vocabulary/executor on a second suitable manipulation task, with
two matched starts and no task-specific executor additions. If it adds little, select
the independent object-relation route from the failures before implementation.
That route must change how Astra expresses or obtains evidence about the relation;
it must not simply rename EEF arrival as placement success.

The next test is not selected because it is easiest to pass. It has a cheap measured
prerequisite and a trace-supported failure prediction, while the relation gap remains
explicitly unresolved. Reassess the portfolio after this one batch. No positive
result is guaranteed; the useful deliverable is a runnable, interpretable comparison
and a revised explanation of what the harness contributes.
