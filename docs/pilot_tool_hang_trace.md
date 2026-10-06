# ToolHang direct-control pilot 001

This is an exploratory trace, not a paired result or a frozen task selection. The native robosuite scene uses Panda and OSC_POSE with the shared RGB-D, calibration and robot-measurement boundary. Astra used a fresh GPT-6 Astra context at medium effort. It could run logged temporary sensor calculations from the first prompt, but chose only image inspection and public JSON reads.

## Verified outcome and resources

Both native goals were true when Astra returned `finish` at step 1855. Frame assembly first became valid at step 900; complete task success first occurred at step 1698 during tool release. All 1855 saved native actions replay with maximum state error 0.0 and the same successful outcome.

The run used 20 returned robot decisions: five sensing commands, fourteen motion commands and one finish. Those decisions required 40 actual inference requests and 20 agent tool calls. Recorded policy-turn time totals 353.274 seconds. Control time is 92.75 simulated seconds, including one second of initial settling. The standard API-equivalent estimate is $2.555356; actual account charges are unknown.

Server elapsed time is 1392.83 seconds. It includes setup, user interruptions and operator/orchestration gaps, and is not an end-to-end comparative speed measurement. Physics paused during policy inference. Do not add simulated time to policy time and describe the sum as measured elapsed time.

Evidence is in `runs/pilot_tool_hang_001`: `outcome.json`, `replay_verification.json`, `diagnostic_summary.json`, `policy_usage.json`, exact policy inputs/outputs, public snapshots and the private action/state trajectory. The local two-view video is retained but ignored by Git.

## Causal trace

| Decisions | Observed event | Interpretation and limits |
| --- | --- | --- |
| 1–2 | Astra selected the frame, queried depth, then closed and lifted. The frame stayed on the table. The requested closing height was 0.836 m; the measured pose reached that target, and the fingers closed almost fully. | The first causal break was grasp geometry, not a wrong object or an unsettled state. Reaching the requested pose did not establish acquisition. An executor cannot choose a better grasp on Astra's behalf. |
| 3–4 | Astra detected the empty grasp, selected a lower target, acquired the frame, lifted and turned its insertion leg down. | Meaningful grasp and reorientation progress without a task-specific routine. |
| 5–7 | Astra measured the stand and transported the frame. The final insertion target was 1.025 m high; the measured gripper stayed near 1.075 m with approximately 22 N raw wrist load. The whole fixed segment ran. | Sustained non-arrival under load is visible in permitted measurements. The load is not a seating certificate. An earlier observation or declared non-progress exit is a possible mechanism, not a demonstrated improvement. |
| 8–9 | Astra released and withdrew; the first withdrawal remained approximately 10 cm from its target and disturbed the stand. It changed withdrawal direction. Frame assembly became valid during the following motion. | Astra recovered. It had to wait for the command boundary to inspect the snag. Assembly was not valid at the earlier release, but became valid at step 900. |
| 10–11 | Astra selected the tool and attempted a grasp. The tool stayed on the table. The approach and descent waypoints ended about 9 cm from their requested poses; execution continued to closing and lifting. | Unlike the first frame miss, this attempt includes substantial non-arrival before a later gripper phase. Fixed duration alone advanced the sequence. A guarded transition could test whether premature phase changes cause retries. Longer fixed execution is a necessary control for that explanation. |
| 12–13 | Astra used the wrist view and depth, changed the grasp target and duration, then acquired the tool. | Second successful recovery; both objects were selected correctly. |
| 14–19 | Astra measured the hole and hook, transported and rotated the tool, released it and withdrew. Native complete success occurred at step 1698 and persisted to the final observation. | Successful precision placement. Several pose targets were not reached exactly, yet the task succeeded. Pose arrival alone must not be treated as object/task completion. |
| 20 | Astra correctly judged completion from its final public images. | No false final completion claim in this pilot. |

All twenty exported tool invocations were manually reviewed. They only read this episode's public sensor JSON or inspect supplied images. No project modification, temporary-code execution, simulator-state access, network use or delegation occurred. This establishes observed compliance for this trace, not a filesystem sandbox.

## What this changes

One success neither establishes a ceiling nor proves that a harness helps. The run supports screening a generic command-boundary question: can measured arrival/non-progress govern when model-selected phases advance or return observations, reducing retries or resource use? It also shows why not to equate an end-effector tolerance with acquisition or task success. No executor should select a grasp, alignment correction or recovery move.

The next pilot uses a different placement seed and a fresh Astra context, with the same sensors, controller, calculation access and episode budgets. Check whether non-arrival before gripper transitions or sustained blocked motion recurs, and whether direct control makes meaningful progress. Use that evidence to select or reject ToolHang before implementing the harness. A credible waypoint baseline and a duration control are required if this mechanism is retained.

The native scorer checks the larger of the tool's two holes. The first instruction said simply “its hole”; this successful run used the scored hole. Future instructions explicitly say “larger hole” to remove that ambiguity. Preserve the original prompt and mark this correction before main evaluation.
