# Interim empirical account

This account is incomplete. The held-out comparison currently has one completed baseline, an interrupted deadline-guard episode and four unstarted episodes. It cannot establish a harness benefit or finish the FYP objective.

## Question and first mechanism

The research question is which communication rules help a foundation model control a robot more effectively. Success, model calls, time and cost are all outcomes; the findings decide which matters. Astra chooses grasps, alignment, phase order and recovery. Sol supplies the simulator and generic executor and analyzes the traces.

The microwave pilot demonstrated useful robot control but did not provide the task difficulty the user wanted. Native ToolHang supplies assembly and precise tool placement without porting a new scene. Two direct pilots yielded one full success and one motion-budget failure. Both contained empty grasps, waypoint non-arrival and blocked insertion. This supported a narrow H3 question: does gating later waypoints on measured robot arrival improve execution or observation handoff?

The frozen executor comparison uses timed waypoints, a deadline guard and an early-arrival guard. All use the same Panda controller, public RGB-D/calibration/robot measurements, temporary calculation access, Astra medium settings and episode limits. Only waypoint termination and cancellation differ. Pose and motion settling are measured; grasp acquisition and object seating are not certified. A deadline control separates gating from early stopping.

## Evidence so far

| Episode | Native full success | Robot decisions | Inference requests | Simulated seconds | Native policy seconds |
| --- | --- | --- | --- | --- | --- |
| ToolHang pilot 001 | Yes | 20 | 40 | 92.75 | 353.274 |
| ToolHang pilot 002 | No, motion budget | 28 | 59 | 120 | 558.930 |
| Held-out start 1, timed baseline | No, policy returned finish | 28 | 56 | 102 | 543.970 |

All three completed traces replay their native simulator states exactly. Pilots informed the hypothesis and are excluded from the held-out comparison. The current protocol has two matched starts and three conditions, six episodes total. The user's budget preference is two starts for future experiments too; a third needs a recorded uncertainty that affects the next design decision. This supports quick mechanism screening, with wide uncertainty and incomplete order balance stated explicitly.

The first held-out baseline advanced through approach and closure before reaching the requested poses, lifted empty, then recovered with a longer and deeper grasp. It assembled the frame and released the tool by its correct larger hole. The tool was visibly suspended, but only 2.51% inserted along the hook and 9.68 mm from the hook line; the native checks require more than 5% and less than 6.75 mm. Astra's final judgment missed that distinction. Physical suspension and benchmark completion must both be reported. This trace shows where robot arrival and task relations differ; it does not show a comparative guard effect.

The deadline-guard episode is interrupted after 15 executed decisions by an Astra usage-limit error. It has no final result. Retain it in the schedule and continue its same state and context when access returns. A policy access interruption is not a manipulation failure.

## What remains to resolve

Complete the frozen matched comparison before changing its interface. Report every outcome, failed placement subchecks, first causal failures and paired resource differences. Successful-completion ratios require both members of a pair to succeed. Total host elapsed includes operator pauses and delivery delay; paused physics and native policy-turn time are separate measurements.

Then retain, revise or discard the arrival-guard explanation. The next mechanism or generalization test must follow the causal traces and be recorded before implementation, with new held-out starts. H1, H2 and H4 remain open; this comparison does not establish sensor-relative correction, command extension beyond a credible waypoint baseline or cross-task delegation. The supervisor account must explain the revised hypothesis and its limits, including null or harmful effects.
