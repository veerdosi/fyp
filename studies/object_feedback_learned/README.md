# Causal learned point measurement

This study tests official scaled-online CoTracker3 on the sensor streams already observed in the six ToolHang episodes. It makes no new Astra requests. The predictor receives RGB and original query pixels; public metric depth and calibration unproject its endpoint pixels. Simulator geometry is confined to replay validation and private scoring.

Read [runtime_account.md](runtime_account.md) for the measured runtime and correction to Sol's real-time criterion. [accuracy_decision.md](accuracy_decision.md) specifies the subsequent endpoint accuracy test before implementation. Original runtime settings and results remain preserved in `probe_protocol.json` and `runtime_result.json`.

The source and checkpoint are pinned in those protocols. The ignored local dependencies are `vendor/co-tracker` at revision `82e02e8029753ad4ef13cf06be7f4fc5facdda4d` and `vendor/checkpoints/scaled_online.pth`, SHA-256 `205d34789f19699d64b22cf93f9b697f15f28d4025240e31532e504109837218`. The checkpoint URL is recorded in `probe_protocol.json`; its publisher is Facebook Research. The existing environment supplies PyTorch 2.14.1 with MPS on Apple M2. No robot-trained policy or simulator truth enters the estimator.

From the repository root, reproduce the runtime probe with:

```sh
.venv/bin/python studies/object_feedback_learned/prepare_probe.py
.venv/bin/python studies/object_feedback_learned/runtime_probe.py
```

The preparation script validates the seeded original initialization and replays the prefix. Do not replace this with a forced state restore: identical physics with different observable sampling phase can produce different camera inputs.

Reproduce the full causal accuracy audit and verification with:

```sh
.venv/bin/python studies/object_feedback_learned/accuracy_audit.py
.venv/bin/python studies/object_feedback_learned/accuracy_report.py
```

`accuracy_protocol.json` checks source and input hashes before inference. The 35 original motion streams retain all 212 queries. Two independent camera predictors reset at each original query frame. Outputs are scored at frame 15, then every eight new frames, with each final partial update retained. Only the newest causal endpoint is scored. The full control-frame availability ledger labels other frames unavailable instead of reporting stale points as current.

The audit saves `endpoint_samples.jsonl.gz`, `availability.jsonl.gz`, per-call RGB chunk hashes/predictions/timing in `accuracy_updates.json`, and exact reconstruction checks in `accuracy_reconstruction.json`. Completed evidence is saved after each episode; `accuracy_progress.json` and `accuracy.log` retain progress. `accuracy_report.py` verifies query/frame completeness, causal endpoints, absence of stale current points, all source hashes and exact replay, and generates a diagnostic ranking and gate figure. Rankings never change the evaluation cohort. This is development on observed traces, not held-out robot-policy evidence.
