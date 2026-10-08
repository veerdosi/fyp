# How returned action reasons guide the next experiment

Read the short `reason` returned with each command together with the preceding
public observation, requested action, achieved motion and next observation. Record
the model's stated expectation, evidence it cites and selected recovery. Use private
geometry afterward to diagnose discrepancies; do not feed that diagnosis back into
an evaluated episode. These records are self-reports, not access to complete internal
reasoning, proof of causal reliance or a substitute for matched experiments.

| Episode / decision | Stated expectation or recovery | Trace evidence | Design implication |
| --- | --- | --- | --- |
| Guard start 2 / 3 | Empty closure; frame remains on table; lower the next grasp | Stop at step 120 cancels close/carry; stop geometry has no fingerpad contacts | A contradiction can trigger a model-chosen recovery without task-specific executor planning. |
| Guard start 2 / 20–21 | Expect hole to rest on hook; then recognize tool fell | Release loses the tool despite EEF arrival | Robot pose arrival does not certify the object relation. |
| Guard start 2 / 23–24 | Empty grasp follows arm non-arrival; approach exposed end from the side | Second stop cancels empty carry after 64.49 mm approach error | Whole-arm feasibility can determine whether a geometrically sensible target is acquired. |
| Timed start 2 / 6–9 | Recognize slip; deepen regrasp and split rotation | Empty-sized warnings during rotation; subsequent regrasp recovers | Baseline can recover with fresh observations; interruption is not the only recovery mechanism. |
| Timed start 2 / 20 | Notice incomplete orientation and request settling | Rotation still 1.342 rad short before settling | Separate model intention from controller feasibility. |
| Timed start 2 / 24–26 | Describe hook through larger opening, then finish | EEF targets reached within 1.5 mm; terminal ring contacts wrong frame section and table | Measure a policy-selected object relation and its uncertainty; EEF progress alone is insufficient. |

The [per-episode causal reviews](account.md) retain the detailed decision references
and public reasons in the original command records. This evidence motivated the
public-point/depth screen, which subsequently failed its frozen gates. It does not
establish that tracking alone would fix semantic target selection or completion
judgment. Each next mechanism needs a prospective prediction and paired test.
