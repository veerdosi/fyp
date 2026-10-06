# Robot policy boundary

Astra's job is to control the simulated robot from permitted observations. It may select sensing pixels and return bounded poses, waypoints, gripper commands, or a completion judgment. It may not create or modify files, develop code, research the project, delegate, or inspect simulator scoring state.

Sol implements the simulator, generic command conversion, validation, sensor handoff, recording, replay and analysis. Sensor files are observation transport. They contain no action hints, inferred task stages, suggested grasps, hidden object coordinates, contacts or reward. All task, object, grasp and recovery choices stay with Astra. The executor may not add task-specific motion rules.

Collaboration agents retain broad tool capabilities, so this boundary is enforced by the policy prompt and checked against their actual tool logs. It is not a filesystem sandbox. The first audit inspected all 14 tool executions through decision 15 of `pilot_microwave_001`: only camera image display and `cat` of public robot or depth-query JSON files occurred. The run retains that audit. Continue auditing each episode and reject policy decisions produced through unauthorized development or oracle access.

Sol's fixed settling period happens before the first policy observation and applies equally across conditions. It corrects an unstable starting measurement; it does not implement a grasp, transport, insertion, or door-closing policy. Changes to the tested executor after pilots must follow the recorded task-selection and evaluation freeze.
