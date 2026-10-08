# Depth uncertainty: completed development screen

The frozen estimator failed the unchanged coverage, precision and loss gates. Local
surface checks removed some bad depth associations, but accepted occluded points
remained common and visible coverage fell below the required 80%. This result rejects
this measurement configuration for precision correction; H1 has not yet had a robot
efficacy comparison.

## Same-sample results

All 212 original queries, 35 streams and 2,757 causal endpoints were retained. The
22,739-frame availability ledger is unchanged. These are correlated development
measurements from the original six episodes, not new held-out robot outcomes.

| Frozen variant | Visible accepted / 1,909 | Coverage | Accepted visible error p95 | Occluded accepted / 339 |
| --- | ---: | ---: | ---: | ---: |
| Original nearest depth | 1,865 | 97.70% | 5.55 mm | 84 / 24.78% |
| Local support and median | 1,500 | 78.58% | 4.88 mm | 56 / 16.52% |
| Primary: local, temporal and other-camera checks | 1,482 | 77.63% | 4.89 mm | 56 / 16.52% |

Gates were coverage at least 80%, accepted visible error p95 at most 3 mm and
occluded false-valid rate at most 5%, required overall, in each camera and in each
observed starting state. Every variant fails all three overall. Primary also fails
the combined gate in every required group. Fixed-camera coverage is 70.77%; wrist
coverage is 93.16%, but its error p95 is 5.66 mm and occluded false-valid rate is
11.63%. The 509 unknown references remain recorded and are not counted as visible
or occluded. No thresholds were changed after scoring.

The primary estimator rejected 478 endpoints for insufficient local support, 228
for a depth discontinuity, 383 for the original tracker visibility flag, 23 for
inconsistent other-camera depth and two for incomplete border patches. Temporal
plausibility rejected none. Adding temporal/camera checks to local support removed
18 visible and five unknown endpoints, with no further reference-occluded rejection.

Of the 56 accepted reference-occluded points, 19 had corroborating other-camera
depth, 27 projected outside that camera and ten had an occluding nearer surface in
that view. Agreement about the reported surface's depth does not establish that it
is the originally selected physical point. This is a measured counterexample to
treating cross-camera depth agreement as an identity certificate. The diagnostic
does not imply that every remaining error has one cause, or that another tracker
will repair thin-surface depth ambiguity.

## Verification and cost

The unchanged nearest-depth control reproduces every original accepted flag,
world point and scoring error exactly. All 10,878 action/state replays and all 49
original queried RGB/depth/calibration snapshots match exactly. Cached outputs are
checked against their causal update logs: output frame equals the last input frame,
with no future input. Both current camera inputs are hashed at measurement endpoints.
Private body-local references are used only for offline scoring; the measurement
module receives public pixels, visibility, depth, calibration and its accepted-point
history.

The complete audit took 244.32 seconds. Computing all three measurement variants
took 0.174 seconds total; per-point combined computation p95 was 0.122 ms. This is
measurement overhead, not tracker latency or robot completion time. The screen used
zero Astra requests and zero new tracker forward calls.

See [result.json](attempt_001/result.json), [configuration](attempt_001/configuration.json),
[reconstruction checks](attempt_001/reconstruction.json) and
[endpoint records](attempt_001/endpoint_samples.jsonl.gz). Reproduce with:

```sh
.venv/bin/python studies/object_feedback_depth/audit.py
```

Reproduction creates a new numbered attempt and preserves the original. The frozen
[protocol](protocol.json) and [selection decision](../tool_hang_v2/next_test.md)
preceded implementation and scoring. The [next decision](next_test.md) now selects
one bounded alternative-tracker feasibility screen; no policy batch is launched
with this failed feedback measurement.
