# Measured waypoint transitions

The selected mechanism uses robot pose and finger velocity only. Object identity, object pose, reward, contacts and native task predicates never drive execution. Astra supplies every pose, orientation, gripper state, waypoint order and duration. The existing OSC_POSE conversion, per-step motion bounds, workspace and episode budgets are shared.

Three execution conditions use the same JSON command vocabulary:

| Condition | Waypoint completion | Next waypoint / observation |
| --- | --- | --- |
| `direct_waypoints` | Run the full requested duration. | Advance regardless of arrival; fresh images after the sequence. |
| `deadline_guard` | Run the full requested duration, then test settled arrival. | Advance only if settled; otherwise cancel the remaining sequence and return fresh images. |
| `phase_guard` | Stop when settled arrival passes, or at the requested deadline. | Advance if settled; otherwise cancel the remaining sequence and return fresh images. |

The guard requires position error ≤3 mm, orientation error ≤0.03 rad, measured end-effector linear speed ≤0.005 m/s, angular speed ≤0.05 rad/s and finger-velocity norm ≤0.001 m/s. All criteria must pass for three consecutive 20 Hz samples and at least ten steps must execute. Speeds use consecutive measured robot poses and the shared control period; finger velocity is the robot observable. A deadline shorter than ten steps cannot pass the guard. These exploratory thresholds were selected before held-out trials. They are execution tolerances, not the scene's insertion tolerance or a guarantee about an object's motion.

Each condition exposes the same `execution.json` fields after motion: requested/executed steps, resolved target orientation, first settled step, terminal pose/speed measurements and cancellation status. This processed robot feedback is available to the timed baseline too. Reports contain no hidden task success. All underlying executor measurements and native actions are retained. A cancelled sequence consumes a robot decision; recovery requires another Astra decision. No automatic new pose, regrasp, insertion search or withdrawal is generated.

The `deadline_guard` control separates the consequence of blocking a transition from ending successful waypoints early. It does not isolate every prompt/planning change caused by these semantics. Both guards can interrupt useful contact motions or fail to certify a grasp. A command timeout merely returns control to Astra.

## Verified mechanics and duration diagnostic

`verify_phase_execution.py` runs actual simulator commands without Astra inference. It holds a sensor-measured robot pose, then reuses the exact first grasp sequence authored in ToolHang pilot 002. The timed condition executes all four waypoints. Both guards cancel the last three when the first approach misses its deadline; the early guard additionally ends the settled hold after ten steps instead of forty. Saved traces use 195, 95 and 65 steps respectively, including initial settling. All replay exactly with maximum state error 0.0. These counts verify semantics, not a task benefit.

The duration diagnostic replays the same pilot grasp from the same start, then repeats with doubled waypoint durations, unchanged targets and order. The original 155-step trace exactly matches the pilot prefix's states and actions. The doubled trace uses 290 steps; approach error falls from 14.28 cm to 0.79 cm and descent error from 7.04 cm to 0.043 cm. Neither acquires or lifts the frame: its centre height changes by approximately 0.000000018 m. Thus tracking lag contributed to non-arrival, while longer execution alone did not repair this particular grasp geometry. This single prefix does not establish a full-task advantage for a guard or exclude duration effects elsewhere.

All five verification/diagnostic runs retain configuration, source hashes, exact commands, raw measurements, actions, snapshots, outcome, reproduction command and exact replay result. See `runs/duration_diagnostic_summary.json`. The verification runs have zero policy inference requests; their legacy `model_calls` field counts operator-submitted commands. They are excluded from main results.
