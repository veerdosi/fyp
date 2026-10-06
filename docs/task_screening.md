# Task screening record

The selection criterion is useful room to test a communication mechanism, not difficulty alone. Astra must make meaningful physical progress; repeated errors must plausibly involve command semantics, feedback, stopping or observation handoff. Sensors, controller, limits and calculation access must match across conditions. Select the evaluation task from traces before implementing a harness, then freeze before held-out trials.

## Microwave demo, retired at user request

`pilot_microwave_001` first satisfied native success at control step 1581 (command 17) and remained successful at the operator stop at step 1915. Astra chose all grasps, recovery, placement and closure actions. Its completion judgment remained unfinished. The saved native actions and simulator states support deterministic replay.

The first causal break was an unsettled starting observation: the mug dropped about 6 cm before grasping. Shared initial settling addresses that protocol error. Astra later encountered empty grasps and blocked insertion, then recovered without a task-specific executor. Those events suggest possible observation or stopping questions, but the successful episode provides no evidence of a success-rate gain from a harness. One success does not establish reliable ceiling performance.

The user requested moving to a different, harder task without a second microwave pilot. `pilot_microwave_002` was stopped after three decisions and 185 control steps. It is an aborted pilot, not a benchmark failure. Both runs received the temporary-calculation permission amendment partway through; neither belongs to frozen evaluation.

## Stacking proposal, rejected before execution

The proposed LIBERO-90 two-bowl stacking task was rejected by the user. No episode was launched. The native evaluator allows placing the lower bowl in the tray before stacking; it does not require transporting an unstable stack. Precision alone had not established a connection to the proposed interface mechanisms, so this proposal supplies no selection evidence.

## Next screening candidate

`libero_90` / `KITCHEN_SCENE1_open_the_top_drawer_of_the_cabinet_and_put_the_bowl_in_it` starts a drawer-access task and requires both an open top drawer and the bowl inside it. It adds constrained articulation before object placement. The native goals and initial states are available in the pinned LIBERO revision.

Screening question: can Astra acquire the handle and make opening or placement progress, yet repeatedly persist against a constraint, lose acquisition, or act on stale geometry until the next handoff? Such a trace could motivate a generic progress or invalidation check and earlier observation. The same trace could instead show a perception, grasp-planning or controller limitation; those outcomes must not be relabeled as interface failures.

Retain the task only if the causal break is observable through permitted RGB-D or robot measurements and occurs with room for recovery. Do not add task-specific grasp, articulation or recovery logic. If direct control succeeds comfortably, or cannot make meaningful progress, discard this candidate. No main task, harness or paired protocol is frozen yet.
