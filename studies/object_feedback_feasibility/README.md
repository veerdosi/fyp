# Object-point measurement audit

This is development using the six recorded ToolHang v1 episodes. It spends zero new Astra calls and does not execute a new robot policy. The [decision](decision.md) records the question, gates and amendments before estimator scoring. Arrival gating remains unresolved; this audit investigates a complementary object-measurement limit.

Run from the repository root:

```sh
.venv/bin/python studies/object_feedback_feasibility/audit.py --validation-only
.venv/bin/python studies/object_feedback_feasibility/audit.py
.venv/bin/python studies/object_feedback_feasibility/report.py
```

The audit uses all 212 recorded pixel queries, grouped into 35 following-motion streams across both starts. Every query is retained. It replays the original native actions from the same seeded initialization and checks every simulator state and all 49 queried camera snapshots. Rendering isolated saved end states, or force-restoring the initial state, changes native observable sampling phase; [the reconstruction diagnostic](reconstruction_diagnostic/result.json) records that difference. The successful reconstruction requires exact RGB, depth and public calibration. Failed reconstruction attempts remain in `reconstruction_diagnostic/`.

`tracker.py` accepts only RGB, metric depth, camera calibration and selected pixels. Its [frozen settings](parameters.json) use pyramidal Lucas-Kanade flow, forward/backward consistency, depth unprojection and permanent loss. The pyramid/window/iteration defaults come from [OpenCV's function documentation](https://docs.opencv.org/4.7.0/dc/d6b/group__video__track.html), inspected on 2026-10-08. Texture, depth, jump and consistency thresholds are this prototype's declared choices. They were not fitted to scored cohort outcomes.

`audit.py` and `camera_reference.py` alone read private simulator geometry to score rigidly transported initial surface points and image-time visibility. A read-only wrapper records references when the original camera sensor samples, preserving its modality, return value and sampling calls. Tracker inputs use the original public convention, including handoff-time calibration. The gate measures error against the current-step object point; image-time error, camera age and initial calibration discrepancy are also recorded. A ray hits an actual surface, which may be a background surface seen through a hole. Body correspondence does not establish that Astra chose the intended semantic tip, hole or object. Unknown reference queries remain explicit.

`cohort.json` preserves the complete query/stream manifest and input hashes. `samples.jsonl.gz` contains every per-step tracker output and private scoring label. `results.json` reports coverage, conditional accuracy and false-valid rate overall and by camera, motion type, start, condition and reference body. Frames and points are correlated, so their counts are not independent robot trials. `sensor_reconstruction.json` records physical and camera replay checks. `verification.json` checks completeness and source hashes; `measurement_gates.svg` and `.png` plot the frozen thresholds.

This code supplies no object feedback executor or task-specific grasp/insertion routine. Any subsequent policy comparison needs its own recorded hypothesis, frozen interface and two new matched starts. A failed gate must remain reported before any estimator revision.
