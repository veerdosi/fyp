# Arrival-guard comparison

The six scheduled episodes are complete: timed waypoints, deadline gating and
early-arrival gating each achieve 0/2 full native successes. No full-task or
successful-completion efficiency benefit is demonstrated on these two starts.
Common placement failures can mask an execution effect; the result does not reject
all arrival gating. The current allocation is in [the research plan](../../docs/research_plan.md).

## Task selection

Selection was recorded on 2026-10-07 before implementation (commit `6d1c496`).
ToolHang reused native robosuite 1.4.1 geometry, Panda OSC_POSE and success checks:
assemble the frame into the stand, hang the tool by its larger hole and release it.
Pilots 400/0 and 401/1 are excluded from evaluation. One succeeds and one reaches
the motion budget, both with meaningful grasp, transport and assembly progress.
Their replayed non-arrival, empty grasp and blocked insertion supported a narrow
command-transition question, not a known 50% success rate or a generic task choice.

Pilot 001's first frame close reaches its requested height but acquires nothing;
a lower grasp recovers. Its later tool approach ends about 9 cm short before closing,
then a measured retry succeeds. Pilot 002 repeats missed acquisition and blocked
insertion, recovers frame assembly, then loses the tool after apparent threading.
The original [pilot 001 summary](../../runs/pilot_tool_hang_001/diagnostic_summary.json)
and [pilot 002 summary](../../runs/pilot_tool_hang_002/diagnostic_summary.json) retain
all requested/achieved waypoints and native goal timelines. Original prompts and
calculations stay with the runs.

## Design and outcomes

[The frozen protocol](protocol.json), [count amendments](protocol.md) and original
protocol versions preserve conditions, starts and the user-requested reduction from
four to two states. Shared sensors, controller, calculation access and limits are
unchanged within the comparison. The [interface reference](../../docs/communication_interface.md#execution-conditions)
explains the three execution conditions.

| Start / condition | Final frame / tool | Decisions | Inferences | Simulated s | Native policy s | API-equivalent USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 / timed | Pass / fail | 28 | 56 | 102.00 | 543.970 | 4.309184 |
| 1 / deadline | Fail / pass | 21 | 45 | 99.00 | 344.068 | 4.195272 |
| 1 / early arrival | Fail / fail | 20 | 41 | 78.95 | 261.645 | 2.526734 |
| 2 / timed | Fail / fail | 22 | 45 | 94.50 | 399.099 | 3.780594 |
| 2 / deadline | Fail / fail | 23 | 48 | 100.00 | 341.974 | 4.377322 |
| 2 / early arrival | Fail / fail | 27 | 58 | 69.45 | 460.063 | 3.972314 |

Each condition's descriptive Wilson 95% interval is [0, 0.658]. Six episodes share
two placements; small samples and incomplete order balance preclude reliability,
equivalence or generality claims. Early arrival consumes less simulated motion,
but requests and native policy time vary. No pair jointly succeeds, so these are
failed-run resource differences, not faster completion. Host clocks contain
interruptions/recovery gaps and cannot establish elapsed-speed gains. Costs are
API equivalents from recorded tokens/rates, not actual account charges.

## Diagnosis and verification

First-start timed control suspends the correct hole but fails shallow/off-axis
engagement. Deadline control hangs the tool but leaves the frame unseated. Early
arrival initially assembles the frame, then joint-limited wrist recovery and
whole-arm contact destroy it. On the second start, deadline release/withdrawal
loses shallow seating, early arrival leaves the frame beside the socket and loses
the tool, and timed control suspends the smaller hole despite larger-hole descriptions.
Per-episode causal reviews and [results](results.json) retain these distinctions.

All six trajectories replay with zero state error; matched initial public inputs
and protocol checks pass. [The official scorer audit](scorer_audit/audit.json)
agrees with all final outcomes and relevant pilot states. Re-executing both original
pilot commands under the then-current execution also matched actions, states and
original outcomes exactly. [The comparison report](verification_summary.json)
remains; duplicated replay directories have been removed because original pilot
actions and trajectories already contain the same data. No stuck-false scorer or physical execution regression is identified.
Native geometric tolerances can reject visible suspension; fingerpad release does
not exclude support from every robot link.

The fixed execution/duration and rejected-budget results remain in
[one verification summary](verification_summary.json); temporary run folders have
been removed. The reusable scripts can regenerate checks outside the repository.
Doubling the original failed grasp's durations
reduces approach/descent error but still acquires nothing. Those records verify
semantics and timing contributions; they are not additional Astra episodes or task
success evidence. Failed-request/recovery details stay in raw run records, with
missing or approximate clock limitations retained in results.

Reproduce analysis with `.venv/bin/python scripts/analysis/analyze_study.py` and scoring with
`.venv/bin/python studies/tool_hang_v1/scorer_audit/audit.py`. Use each run's recorded
replay command for physical replay. No reproduction step requests Astra decisions.
