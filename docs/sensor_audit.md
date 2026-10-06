# Sensor audit: LIBERO microwave task

The fresh Mac environment rendered the standard task and recorded a 40-step fixed sequence. Its action replay reproduced every flattened MuJoCo state with maximum absolute error 0.0. Evidence: `runs/smoke_001/replay_verification.json`. This is simulator verification, not task success.

## Policy and executor boundary

The policy receives RGB and metric optical-axis depth from `agentview` and `robot0_eye_in_hand` at 256 by 256 pixels, end-effector position and quaternion, seven joint positions and velocities, two finger positions and velocities, and raw wrist force and torque. The force and torque sensors are present in the Panda XML, but not in LIBERO's default observation dictionary; the wrapper reads robosuite's `ee_force` and `ee_torque` properties and adds them explicitly. These measure local wrist loads including dynamics. They do not certify object acquisition.

Camera images are flipped vertically into the conventional top-left origin. Metric depth conversion and camera calibration use robosuite's camera utilities. Pixel queries unproject depth through camera intrinsics and calibrated camera-to-world transforms. They do not identify objects. Calibration is ideal in this simulation. The moving wrist camera transform comes from simulated robot kinematics; this assumes accurate robot proprioception and known camera mounting, not an estimated object pose. No noise or calibration error is claimed to have been evaluated.

The direct executor uses measured end-effector pose to realize a fixed model-selected absolute pose through native OSC_POSE delta actions. It uses no vision, object estimate, reward, contact truth, or task stage. It executes the full declared duration. It can validate commands and enforce common target bounds, 0.015m translation and 0.15rad orientation updates at 20Hz. A target bound is not a collision-avoidance planner.

## Excluded simulator information

Default LIBERO observations include each mug's world position, quaternion and pose relative to the gripper, plus an `object-state` vector. None is present in the public policy folder. These are written only to step diagnostics. MuJoCo state, task reward, collision contacts, task predicates and success are also excluded from policy inputs and execution decisions. Task success is checked after execution for scoring; it does not end an episode automatically.

Every control step records the pose and finger/load measurements used by the executor, the native action, post-step robot readings, and separate diagnostic object observations. Camera RGB-D is saved at each model handoff; the direct executor does not consume camera frames during motion. A two-view video records every control step. Saved initial state, actions and state trajectory support deterministic action replay.

## Pilot scope

Physics is paused during model calls. These pilots measure bounded robot decisions, not real-time robustness to inference delay. Sensing-only decisions count against the same policy-decision budget as motion decisions. Native agent sessions expose per-request token records and turn timing. `policy_usage.json` distinguishes policy decisions from model inference requests, which also include requests surrounding image and sensor-reading tool calls. It records a standard API-equivalent estimate using documented Astra rates, with actual account charge left unknown. A fixed non-model verification sequence uses zero model calls.

See [policy_boundary.md](policy_boundary.md) for the restriction against Astra file writes, code development, or simulator-state access and its tool-log audit.
