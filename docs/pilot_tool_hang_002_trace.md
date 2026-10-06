# ToolHang direct-control pilot 002

This exploratory run used a fresh GPT-6 Astra context at medium effort, seed 401 and placement index 1. The initial prompt specified the larger tool hole. The same Panda, OSC_POSE controller, public RGB-D/calibration/robot sensors, calculation tools, 30-decision limit and 2400-step limit were used. Code revision was `09702d5`.

## Outcome and resources

The run exhausted its motion budget at step 2400. Frame assembly first became valid at step 1604. Tool hanging and complete success never became valid. Astra did not return a final completion judgment before the budget stop. All 2400 native actions replay with maximum state error 0.0 and the same unsuccessful outcome.

There were 28 robot decisions, 59 actual inference requests and 31 agent tool calls. Native completed-turn durations total 558.930 seconds. Motion consumed 120 simulated seconds, including one second of initial settling. The standard API-equivalent estimate is $4.961720; actual charges are unknown.

The server elapsed 11789.617 seconds. This interrupted exploratory run includes a long operator/orchestration gap and cannot support an end-to-end speed comparison. Dispatch-to-delivered-response timestamps total 1090.922 seconds, including message delivery delay. They are distinct from the agent's completed-turn duration. Command execution and recording took 50.449 seconds; setup and settling took 2.410 seconds. Physics paused during policy work and operator gaps.

## Trace and causal limits

| Decisions | Observation | Interpretation |
| --- | --- | --- |
| 1–2 | Correct frame selection and depth queries; approach ended 14.28 cm short and descent 7.04 cm short. The subsequent closing pose reached within 3.1 mm, but the lift was empty. | First causal break: grasp acquisition. Premature sequence transitions recur from pilot 001, but the final closing geometry also matters. A pose guard cannot certify acquisition or choose a better grasp. |
| 3–8 | Astra lowered and reacquired the frame, lifted it, then calculated an axis correction from public depth points and robot pose. | Meaningful progress and model-owned geometric computation. |
| 9–13 | A requested insertion pose was reached, yet assembly remained invalid. Release/withdrawal moved the frame with the gripper; Astra regrasped and measured again. | Pose arrival did not establish seating. Tool/shaft motion relative to the gripper can invalidate a rigid-offset calculation. |
| 14–16 | Two insertion attempts ended 10.60 cm and 6.48 cm short of the requested position. | Repeatable sustained non-arrival, visible in permitted robot measurements. Raw loads include dynamics and cannot certify seating. Earlier handoff is testable. |
| 17–19 | Withdrawal remained 6.87 cm short, then the frame settled into a valid assembly during the tool approach. Astra acquired and lifted the tool. | Assembly succeeded through model-selected recovery. Closing also followed substantial tool-approach non-arrival; later acquisition nevertheless succeeded. Guards could prevent useful contact-assisted motions as well as bad transitions. |
| 20–24 | Astra calculated tool reorientation, transported it, measured the hole and hook, attempted threading and released. The tool fell flat onto the table. | Placement/alignment failure despite near-arrival at the final pose targets. A robot-pose transition guard is not expected to solve this by itself. |
| 25–28 | Astra noticed the fall, sensed again, regrasped, lifted and released near the hook. The remaining 220 steps were consumed; hanging stayed invalid. | Recovery remained with Astra. Count this as a budget-limited failure, not successful partial assembly. |

All 31 exported tool invocations and all three calculation sources/outputs were reviewed. Reads were public sensor images/JSON; writes were temporary calculation programs in `policy_compute`, executed through the logging wrapper. Calculations used NumPy/SciPy on literal public sensor coordinates and measured poses. No repository modification, simulator/scoring access, network use or delegation was observed. This is an observed boundary audit, not a filesystem sandbox. Available-input manifests are not traces of actual file reads.

Evidence: `runs/pilot_tool_hang_002/outcome.json`, `diagnostic_summary.json`, `policy_usage.json`, `policy_tools_complete.json`, calculation logs, exact prompts/commands, public snapshots, native trajectory and `replay_verification.json`.

## Selection implication

Together the pilots show useful physical progress, one complete success and one budget-limited failure. Non-arrival before later phases and blocked insertion recur. These support selecting ToolHang for a narrow command-transition/handoff experiment. They do not establish a success rate or show that the proposed mechanism will improve the final hole alignment. Record the mechanism before implementation and freeze the comparison before held-out model runs.
