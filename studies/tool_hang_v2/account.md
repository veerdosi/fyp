# Empty-closure handoff: completed screen

All four scheduled episodes finished and replay exactly. Guarded control achieved
2/2 native successes; timed control achieved 0/2. The first pair has an initial-prompt
confound, so only the second pair is a clean matched comparison. On that start,
guarded control succeeded after two empty-grasp interrupts; timed control recovered
a grasp slip but finished with the tool contacting the wrong frame section and the
table. This is a promising single comparison, not an established success-rate gain.

## Prediction and controlled difference

The [prerecorded decision](decision.md) predicted that cancelling a model-declared
close/carry continuation after stable empty-sized closure would prevent stale empty
transport and return control to Astra for recovery. The [frozen protocol](protocol.md)
uses two new starts, 601/31 and 602/32, under timed and guarded execution. Astra medium
has a fresh context per episode, 30 robot decisions and 2400 steps at 20 Hz, including
20 settling steps. Both conditions have the same RGB-D, calibration, robot readings,
processed sensor feedback and logged temporary calculation access.

Both accept the optional declaration. Timed control reports the warning at normal
handoff; guarded control cancels the current and remaining waypoints and supplies
a fresh observation. Astra selects every grasp, target, phase and recovery. Force
and stall flags are advisory. Neither acquisition nor seating is certified by the
executor, and private task checks never reach the policy or controller.

## Every scheduled outcome

| Start / condition | Native frame / tool | Decisions | Usage-recorded inferences | Simulated s | Native policy s | API-equivalent USD | Interrupts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 / timed | Pass / fail | 29 | 59 | 119.50 | 489.179 | 4.877772 | 0 |
| 1 / guarded | Pass / pass | 18 | 37 | 59.75 | 271.145 | 2.574790 | 0 |
| 2 / guarded | Pass / pass | 28 | 59 | 108.75 | 1008.701 | 6.054358 | 2 |
| 2 / timed | Pass / fail | 26 | 53 | 103.00 | 570.189 | 4.021458 | 0 |

The descriptive 95% Wilson intervals are [0, 0.658] for timed and [0.342, 1] for
guarded. They include the confounded first pair and cannot support a controlled
population effect. There is one clean success difference, +1 for guarded. No pair
has two successful conditions, so no successful-completion resource ratio exists.
On the clean start, guarded consumed six more usage-recorded inferences, 5.75 more
simulated seconds and about $2.03 more API-equivalent cost. These describe the
success/failure tradeoff, not a speed gain or an established cost of improvement.

Native policy durations include tools and a failed usage-limit turn in the second
guarded episode. Actual account charges and unrecorded rejected-request costs are
unknown. Host totals were 21227.032, 1366.880, 20750.317 and 2647.815 seconds in
scheduled order; simulator command totals were 45.188, 25.211, 48.971 and 48.084
seconds. Host totals include operator/service interruptions and root analysis;
recovered origins are approximate. One dispatch/delivery interval is missing in
each second-start episode. The analyzer keeps those aggregate intervals and
orchestration residuals null. Physics pauses during inference. None of these host
numbers establishes end-to-end completion speed.

## What the mechanism actually did

The first guarded success had no interrupt. Astra noticed a nearly empty initial
closure at normal handoff, retried, then cited stalled insertion/contact load before
a lateral correction. Success cannot be attributed to an interrupt that never
occurred. Shared processed feedback may have helped, but its contribution was not
isolated from raw sensors, policy variation or the first-pair prompt mismatch.

On start 2, the guard stopped an empty frame closure at step 120 and an empty tool
recovery closure at step 1725. It cancelled 50 and 55 requested steps respectively,
including both queued lifts: 105 steps / 5.25 simulated seconds. Private saved-state
geometry shows no fingerpad contacts in the three samples ending at either stop.
Astra cited the first empty closure before a lower regrasp, and attributed the
second to arm non-arrival before choosing a side approach. The rule therefore
performed its intended invalidation/handoff function; recovery remained with Astra.

The clean timed baseline initially lifted the frame but lost it during rotation.
Its armed empty-sized warning appeared at step 271; the command continued through
step 380. Astra then recognized the loss and recovered with a deeper grasp and
staged rotation. This demonstrates a relevant warning opportunity, without proving
what the entire episode would have done under a different policy history.

Both timed runs failed the final tool relation. Start 1 ended with the tool on the
stand base, 23.72 mm from the hook line. Start 2 declared that the larger hole was
hanging, but that ring contacted `frame_grip_frame` and the smaller ring contacted
the table. Its larger-hole center was 43.75 mm from the hook line, versus the native
6.75 mm limit; horizontal-hook contact and straddling failed. Guarded final states
contacted the horizontal hook through the larger ring and passed both native checks.
Rebuilt contacts are geometry, not reconstructed load forces. Native success was
not redefined to reward visible suspension.

The guard does not directly correct these placements. Start 2 guarded also released
a tool that fell, then recovered it and chose a different final approach. Thus the
observed clean-pair win is compatible with useful early handoff, but does not prove
that those two stops caused the final seating advantage or that the advantage will
repeat. No third or replacement start was added.

## Integrity and revised explanation

Initial physics, actual public images/depth/calibration, robot readings and processed
feedback match within both starts. The second pair's saved common instructions match
after normalizing paths and the declared execution difference. [Amendment 002](amendment_002_encrypted_input_erratum.json)
preserves the first baseline's unverified shorter initial prompt; encrypted native
archives were not decrypted. Keep the first pair exploratory.

All four trajectories have zero state/sensor/calibration replay error, with native
scoring and processed monitor/action rows exact. Both second-start episodes needed
same-context reconstruction after intentional root interruptions; all retained
original robot/object/scoring records and final images matched exactly. Original
full hidden prefix arrays were not retained, so they are not independently verified.
Their final recovered trajectories replay exactly. Already-completed policy outputs
were relayed unchanged, without another inference or budget reset. All exported
policy tool inputs and calculation sources/outputs were manually reviewed; access
was limited to permitted public files and own calculations. This is an instruction
and audit boundary, not an OS sandbox.

Retain empty-closure invalidation as a narrow, demonstrated mechanism. The task-level
comparison is encouraging but uncertain, and supplies no efficiency result. Revise
the broader theory: a useful communication contract needs both an observable way
to invalidate a contradicted expectation and a way to express and measure the object
relation being controlled. Robot arrival, non-empty opening and a plausible finish
description cannot supply that relation. The reasons attached to commands help
identify expectations and recovery choices, but are self-reports, not complete
internal reasoning or evidence of causal dependence by themselves.

The next substantial experiment should examine a different bottleneck, rather than
tune this finger threshold. The [next-test decision](next_test.md) records the bounded
measurement question and its consequences before implementation. H1 remains a
candidate; the FYP is not finished by this small batch.

Reproduce and inspect evidence using [README.md](README.md), [results.json](results.json),
[native geometry](native_terminal_geometry.json), [stop geometry](interrupt_geometry.json)
and [terminal contacts](terminal_support_geometry.json). Per-run `causal_review.json`
retains the command/recovery account and clock limitations.
