# Two-start empty-closure handoff comparison

The [selection decision](decision.md) is recorded before any new start is inspected or any policy episode is launched. [protocol.json](protocol.json) freezes all code/material hashes, counts, order, sensors, parameters and budgets. Both original manipulation pilots and v1 outcomes remain distinct evidence.

| Order | Episode | Seed / state | Condition |
| --- | --- | --- | --- |
| 1 | th_v2_s01_timed | 601 / 31 | Full-duration waypoints with shared feedback |
| 2 | th_v2_s01_guard | 601 / 31 | Same feedback with optional armed empty interrupt |
| 3 | th_v2_s02_guard | 602 / 32 | Same feedback with optional armed empty interrupt |
| 4 | th_v2_s02_timed | 602 / 32 | Full-duration waypoints with shared feedback |

Astra uses fresh GPT-6 Astra medium contexts. Each episode has 30 robot decisions, 2400 control steps including 20 initial settling steps, and the same logged temporary calculations. Four episodes implement two matched starts. No third is planned. Astra owns every grasp, phase, declaration, target and recovery. The generic executor cancels only when the optional armed empty-sized closure rule fires; it does not correct the grasp or choose a new target.

Both conditions receive the same raw sensors, compact processed feedback and optional full 20Hz measurement rows. Compensated wrench and progress are advisory. The timed baseline may request separate close/observe moves, and both may use one to four short waypoints. The comparison includes the policy's response to the different stopping semantics; it is not replay of identical policy actions.

The primary outcome is full native terminal success. Intermediate empty-transport prevention, model calls and costs are reported separately. Compare completion resources only on jointly successful pairs. Two starts support descriptive mechanism discovery with wide uncertainty. Preserve every scheduled result, service fault, policy completion claim and retry within its original shared budget. Successful fixed fixtures establish implementation behavior, not task benefit.

Run a scheduled episode with:

```sh
.venv/bin/python scripts/episodes/start_feedback_episode.py th_v2_s01_timed --port 8765
.venv/bin/python scripts/policy/prepare_feedback_policy.py runs/th_v2_s01_timed
```

Sol dispatches the saved sensor-only prompt to a fresh medium-effort Astra agent and relays every unaltered returned command with the existing logging tools. Do not invoke the policy during setup or verification. After each motion, read the same public feedback files in both conditions; private native scores remain unavailable to the policy. Record actual native inference usage rather than treating robot decisions as inference count.

The fixed publication verification in this directory confirms the two conditions expose equal processed data when actions match and preserves exact source action/state prefixes. The mechanism's positive and negative paired fixture results are in `studies/robot_feedback_modalities/guard_verification_result.json`; temporary fixtures were removed during cleanup. A whole-task result and revised theory remain necessary; this protocol is the next stage, not the whole FYP.

## Input logging erratum

[Amendment 001](amendment_001_dispatch_logging.json) attempted to recover the first dispatched prompt from the native archive. [Amendment 002](amendment_002_encrypted_input_erratum.json) corrects that attempt: the archive contains ciphertext, not recoverable plaintext. The first scheduled timed episode retains its exact actions, outputs and subsequent plaintext follow-ups, but its initial prompt cannot be verified or matched. Report the first pair as exploratory with this confound. The remaining initial dispatches use the saved preparation exactly; only episode paths, sensor readings and declared condition semantics change. The second start supplies one clean matched pair. Keep all four scheduled outcomes and original parameters; do not add replacement episodes.
