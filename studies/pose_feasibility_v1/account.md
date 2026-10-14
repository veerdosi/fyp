# Pose-feasibility query comparison

All four corrected scheduled episodes are complete and audited on two matched
starts. Baseline succeeded on 1/2; preview succeeded on 0/2. The structured query
has no demonstrated contribution in this screen and is retired from the current
research allocation. This does not establish that the query causes failure or
that all bounded delegation is ineffective. No third start is required.

| Start | Condition | Full success | Decisions | Inferences | Simulated seconds | Native policy seconds | API-equivalent USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Waypoints | Yes | 18 | 36 | 79.8 | 250.061 | 2.600678 |
| 1 | Preview | No | 30 | 59 | 114.4 | 463.015 | 4.933024 |
| 2 | Preview | No | 28 | 59 | 103.75 | 587.589 | 5.692494 |
| 2 | Waypoints | No | 28 | 58 | 95.6 | 451.906 | 5.333772 |

Both conditions use the same controller, sensors, robot model/calculation helper,
temporary calculation access, execution limits and explicitly armed empty-closure
interrupt. The preview condition adds one optional structured bounded pose-search
query. Astra chooses every candidate, action and recovery. The query changes no
physics and supplies no object, contact or task certificate.

The prospective prediction concerns avoidance of unsupported robot targets and
wasted recovery. Each preview episode used one query with two candidates; all four
candidates had solutions, and each queried approach was subsequently reached.
No unsupported-candidate warning or avoidance has been observed. Thus the proposed
warning pathway has not engaged in these episodes. Successful pose search did not
prevent later grasp, contact, clearance or placement failures.

On start 1, preview control assembled the frame but left the tool on the base;
the baseline completed both relations. On start 2, preview control acquired both
objects and recovered blocked movements, but released the frame without native
assembly and finished with shallow, off-axis larger-hole suspension. The tool was
visibly hanging and released: its native hook-line distance was 11.41 mm versus
6.75 mm tolerance, and insertion was 2.17% versus a 5% minimum. The frame tip was
131.44 mm from the stand base versus a 50 mm maximum and outside the opposed walls.
Neither native relation ever passed in that episode. These measurements are
offline diagnosis, never policy inputs.

All four completed episodes replay exactly, including actions, public sensors,
calibration, processed feedback, native checks and query results. All 108 exported
tool invocation bodies have been manually reviewed. The second pair used five
logged NumPy/SciPy calculations from public selected coordinates and measured
poses; no prohibited access was observed. This is an instruction/audit boundary,
not an OS sandbox. Saved common prompts and initial public inputs match after
path/capability normalization. Native encrypted initial dispatch storage prevents
independent automated plaintext equality; saved text is manually copied verbatim.

Start-2 preview resumed its original policy context and remaining budget after
exact reconstruction of 1,850 retained action steps. Original robot/object records,
native scoring, feedback and final images match exactly. Original complete hidden
prefix arrays were unavailable; the rebuilt full prefix is reconstruction rather
than independent retained-state proof. The pending original decision was executed
without another inference. Its dispatch/delivery interval is unavailable, so
complete delivery aggregates and orchestration residuals are null, not zero.
Native completed-turn duration remains measured separately.

Host elapsed includes long interruptions and cannot support a completion-speed
claim. API-equivalent estimates use the recorded rates and measured tokens;
actual account charges are unknown. There are no jointly successful
pairs for completion-resource ratios. Lower resource consumption by a failed
condition would not establish faster completion. Both pairs execute preview first,
and two starts provide wide uncertainty rather than a general reliability estimate.

Reproduce motion verification with the command in each episode's
`replay_verification.json`, then regenerate the descriptive ledger with
`.venv/bin/python studies/pose_feasibility_v1/analyze.py`. After running the common
episode summarizer, apply `finalize_clock.py RUN` to preserve unavailable delivery
intervals in derived clocks. The [batch decision](decision.md) records the next necessary discriminator;
another grasp-interruption experiment is not scheduled.


On start 2, baseline recovered two empty frame attempts, acquired the frame and
tool, then stalled during insertion and withdrawal. The tool fell after release
and a recovery attempt left it caught low on the stand shaft. Astra correctly
acknowledged failure at decision 28. The frame tip ended 120.03 mm from the base;
the larger hole was 145.40 mm from the horizontal hook line and had no hook
contact. Neither relation ever passed. Baseline also resumed its original context
and budget after exact 1,912-step observable reconstruction; original complete
hidden prefix arrays were unavailable and its host origin is approximate.

The preview-minus-baseline resource differences were +12/+0 robot decisions,
+23/+1 inferences, +34.60/+8.15 simulated seconds, +212.954/+135.683 native policy
seconds and +$2.332346/+$0.358722 API-equivalent across starts 1/2. Neither pair
jointly succeeded, so these are descriptive consumption differences, not
completion-efficiency ratios or a causal cost of the query.

Waypoint nonarrival fractions were baseline 5/30 versus preview 9/44 on start 1,
and baseline 15/42 versus preview 8/39 on start 2 (3 mm / 0.03 rad exit tolerance).
The second preview had fewer nonarrivals but still failed both task relations.
It also used a different motion sequence; the queried approach alone does not
identify a causal benefit for subsequent motions. The intended warning-avoidance
pathway was never observed. No task or resource benefit meets the prospective
criterion, and no further query/guard variant is scheduled.

Descriptive 95% Wilson intervals are [0.095, 0.905] for baseline and [0, 0.658]
for preview. These broad marginal intervals and two stochastic policy episodes
per condition do not support a general reliability estimate, equivalence claim
or significance claim. Retain the null contribution result at this tested scope.
