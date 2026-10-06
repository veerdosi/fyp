# Task and mechanism selected from pilots

Selection recorded on 2026-10-07, before implementing a candidate executor or running held-out policy episodes.

Use native robosuite 1.4.1 `ToolHang`. Preserve its scene, Panda, OSC_POSE controller, native success checks and instruction: assemble the hook frame into the stand, then hang the tool by its larger hole on the hook and release it. Pilot placements (seed/index 400/0 and 401/1) are excluded from evaluation.

The two pilots provide the required scope: Astra assembled the frame in both, acquired and transported both objects, and completed the full task in one. Both advanced fixed waypoint sequences despite substantial preceding non-arrival and encountered sustained blocked insertion. Public robot measurements expose those execution events; private geometry/contact predicates score task progress and success. This is sufficient to test a mechanism, not evidence that it works.

Test a small revision of H3: measured pose/gripper settling can govern advancement through Astra-selected waypoints; non-arrival or non-progress can cancel the remaining sequence and return fresh observations. The executor retains the existing pose servo and may neither select targets nor repair a grasp. Robot arrival is only an execution event, never object acquisition, seating or task success.

Predicted effect: fewer harmful phase advances and fewer wasted control steps may allow more successful recovery within the same episode budget. Extra handoffs, strict arrival requirements and interruption of useful contact motions may instead increase calls or reduce success. Pose guards are not expected to fix incorrect grasps, changes in held-object geometry or final hole alignment that fails despite pose arrival.

Compare a strong timed waypoint baseline with guarded waypoints on matched held-out starts, fresh contexts and the same model, sensors, computation access, controller and hard budgets. Preserve the actual inference-request accounting. Include a fixed longer-duration control for the pilot grasp prefixes to determine whether tracking lag alone explains the non-arrival. That diagnostic uses Astra's already-recorded targets, no new task routine and no model; it is not a task-success comparison.

The comparison must report native full success on every trial, first causal failures, decisions, inference requests, simulated motion, native policy-turn duration, delivered-response delay, host execution/orchestration time, tokens and API-equivalent cost. Report null and negative outcomes. Main counts, starts, thresholds, conditions and analysis rules will be frozen in a separate protocol after implementation verification and before held-out policy runs. Generality across tasks is not claimed by this initial ToolHang test; H4 remains open. H1 sensor-relative correction and H2 longer sequences are not isolated here.
