# Next decision after the depth screen

Recorded after attempt 001 completed, before installing or running TAPNext++.

Local depth checks improve the observed error tail and loss rate, but destroy
enough fixed-camera coverage to fail the gate. Other-camera agreement does not
resolve correspondence identity: 19 accepted reference-occluded points are
corroborated. This supports one alternative correspondence/visibility screen, while
also warning that depth support and thin geometry remain independent limitations.
Do not spend another robot-policy batch on this estimator or tune its thresholds.

Use the official Google DeepMind TAPNext++ VOTSp2026 implementation and its public
512-resolution checkpoint. Its recurrent frame-by-frame interface addresses causal
correspondence and visibility. The benchmark claim does not establish local Mac
feasibility or robot precision. Inspect and pin the source revision, checkpoint hash,
coordinate conventions, visibility threshold and official local support grid before
accuracy scoring.

First run one bounded feasibility probe on the already verified public RGB/query
archive. Use MPS, float32, no compilation or CUDA autocast. Preserve the official
512 input resolution, 64 support points per query and radius 32 in input coordinates.
No retraining, alternative checkpoint, grid/threshold tuning or resolution reduction.
Do not enable silent CPU fallback. If MPS rejects an operation, retain the error and
make at most one explicit CPU compatibility attempt with identical model settings.
Allow paused physics; measure actual latency and memory rather than reviving the
withdrawn 0.4-second exclusion. A ten-minute runtime limit for this small probe is
an engineering expenditure bound, not a scientific accuracy threshold.

If feasible, freeze one full observed-cohort screen before scoring. Run every
original query forward causally, with no future frames or private identity used for
prediction. Score the same 2,757 endpoints with the unchanged primary depth policy,
coverage/precision/loss gates and required groups; retain availability at intermediate
frames separately. Report original-depth and local-only diagnostic controls as well.
The model's immediate outputs may improve update availability, but availability
cannot substitute for precision or correct loss detection.

If the one candidate cannot run within local resources, or fails the fixed accuracy
gate, retire this tracked-surface correction route for this iteration. Choose a
different representation or embodiment/feasibility mechanism from recorded robot
failures before implementation. This is a bounded prerequisite screen, not another
sequence of tracker variants. A passing development measurement would still require
an explicit correction command, verification and two new matched Astra starts.

Sources inspected before the probe:
[official README](https://github.com/google-deepmind/tapnet/blob/main/tapnet/tapnextpp/votsp2026/README.md),
[wrapper](https://github.com/google-deepmind/tapnet/blob/main/tapnet/tapnextpp/votsp2026/model.py),
[support-grid runner](https://github.com/google-deepmind/tapnet/blob/main/tapnet/tapnextpp/votsp2026/tracker.py).
