# Robot feedback alternatives and bounded empty-closure prototype

The [decision](decision.md) explores robot progress, finger opening and compensated wrist load independently of point tracking. [account.md](account.md) reports two fixed calibrations and the complete six-trace sensor screen. The [monitor decision](monitor_decision.md) freezes sensor rules before private contact context is read; [guard verification decision](guard_verification_decision.md) selects the smallest bounded mechanism before implementation.

No Astra calls are used for calibration, recorded-trace screening or fixed prototype verification. These are Sol's experiment/verification motions and arithmetic, not replacement task policies. Native success is recorded but is not a calibration/fixture success criterion.

From the repository root:

```sh
.venv/bin/python studies/robot_feedback_modalities/calibrate.py
.venv/bin/python studies/robot_feedback_modalities/replay.py --run studies/robot_feedback_modalities/calibration_s01
.venv/bin/python studies/robot_feedback_modalities/replay.py --run studies/robot_feedback_modalities/calibration_s02
.venv/bin/python studies/robot_feedback_modalities/screen.py
.venv/bin/python studies/robot_feedback_modalities/report.py
.venv/bin/python studies/robot_feedback_modalities/verify_guard.py
```

Creating fixed runs requires fresh output directories. Existing outputs are preserved rather than overwritten. The frozen calibration driver printed an unsupported `--replay-only` option in its original replay metadata; the standalone `replay.py` above reproduces and corrects that command while leaving actions, sensors, outcomes and calibration source intact.

The screen keeps all public measurements in `monitor_samples.jsonl.gz`. `private_contact_context.jsonl.gz` is scoring/diagnosis only; contacts are recomputed from saved geometry, not reconstructed force labels. Protocols record source/input hashes, all thresholds, pose schedules and counts. Complete results retain every signal and every waypoint, including intentional empty closure and missed proximal collisions.

`src/fyp/sensor_monitor.py` is the generic sensor-only monitor used by the prototype. The original study's identical `monitor.py` remains frozen for provenance. `src/fyp/grip_guard.py` extends native timed waypoints with optional `abort_if_empty_close`. It can cancel and return fresh observation when Astra explicitly arms the empty-sized rule. It does not choose grasps, targets, phases or recovery. Load/progress signals are advisory in this prototype. “Not empty-sized” is never reported as proof of acquisition or task success.

The two fixed fixture cases each compare shadow reporting with armed interruption, retaining all four outputs. They use previously recorded Astra poses and observations, so their outcomes establish runnable command behavior only. Any new policy comparison must use its separately frozen two-new-start protocol and fresh medium-effort Astra contexts.
