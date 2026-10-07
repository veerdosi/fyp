# Next necessary test: learned online tracker runtime and causality

Recorded on 2026-10-08 after the complete frozen local-flow audit, before implementing or running this probe. It uses recorded public sensor data and zero new Astra calls. Arrival gating remains unresolved; the failed flow prototype is preserved separately.

## Question and reason

The local tracker accepted occluded or drifting points despite a small forward/backward residual. Coverage, precision and false-valid acceptance all failed the original gate. Before abandoning a public point-measurement route, check whether a stronger generic tracker with learned visibility can run causally at a useful rate on this Mac. This is a measurement component, not a learned task/grasp policy, and would be shared by future comparison conditions.

Use the official [CoTracker3 repository](https://github.com/facebookresearch/co-tracker), inspected on 2026-10-08. Its online predictor uses a 16-frame sliding window with an eight-frame step and a default combined visibility/confidence threshold of 0.6. The [online demonstration](https://github.com/facebookresearch/co-tracker/blob/main/online_demo.py) supports an MPS device. Local PyTorch 2.14.1 reports MPS available. These facts justify a runtime probe, not an assumed accuracy or control benefit.

## Predefined probe

Pin the repository revision and official scaled-online checkpoint hash before inference. Use official model resolution, six refinement iterations, the 16-frame window, eight-frame update step, combined threshold 0.6 and a regular six-by-six support grid. Do not train, tune thresholds or use object names, segmentation, geometry, scores or other private inputs. Retain both cameras and every original query from the first complete cohort stream; use its first 64 recorded motion frames after the query plus the original query frame. This chronological prefix is chosen for compatibility and runtime, not as a favorable accuracy subset.

Supply only frames already available at each update. Initialize from the query frame; process chronological overlapping windows and use only the latest available endpoint prediction for prospective control. No future image or backward/offline inference is permitted. Account for the 16-frame bootstrap and eight-frame update spacing at 20 Hz; old predictions cannot masquerade as current measurements.

Record source/checkpoint/input hashes, device, model settings, prediction shapes and finite outputs, all update timings after device synchronization, bootstrap duration, output timestamps and observed allocated memory. Separate loading/warm-up from steady updates. The runtime criterion is combined steady two-camera p95 update time at most 0.4 seconds, the eight-step acquisition interval. If compatibility, causality or this rate fails, do not build a continuous point-feedback executor on this configuration; record the limitation and revise the interface question.

If the probe passes, record and freeze a separate complete development-cohort audit before implementation. Retain all 212 queries, the original 80% coverage / 3 mm p95 error / 5% false-valid gates and all categories. Score causal endpoint availability and between-update unknown/age explicitly; do not retrospectively score older predictions with later images. This would still be development on observed starts. Only a passing, usable measurement source can justify a new frozen robot comparison with two new matched starts, equal processed/raw sensing and computation access, and Astra owning every robot decision.
