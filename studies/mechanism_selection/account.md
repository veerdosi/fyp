# Select a robot-feasibility query, not a rigid-motion compiler

The retrospective discriminator supports testing a bounded pose-feasibility query.
The inspected calculations do not establish a geometric bookkeeping failure that
would justify implementing the proposed pivot command. Three troublesome wrist
targets instead fail a fixed robot-only IK search, while a target from the final
wrong placement passes. This selects a planning aid with explicit limits, rather
than a task-success or collision certificate.

## Evidence separating the explanations

All four recorded public calculation outputs reproduce exactly. The three rod
corrections use a rotation aligning the measured axis downward and rotate the
point-to-EEF offset consistently. They are coherent rigid-transform calculations,
although this does not certify their selected pixels or physical attachment. Their
requested orientation errors at exit were approximately 1–2 mrad. The successful
frame corrections provide no demonstrated arithmetic error for a compiler to fix.

| Recorded event | Evidence | Consequence |
| --- | --- | --- |
| Guarded start 2, turn at decision 14 | 40.45 mm position and 0.170 rad orientation error; next target at decision 15 arrives | Pose/context can matter independently of intended orientation. |
| Timed start 2, turn at decision 19 | 32.28 mm and 1.342 rad error; still moving at expiry | Duration/non-arrival contributes; this waypoint was not already at a joint bound. |
| Timed start 2, settle at decision 20 | 46.27 mm and 0.108 rad error; last joint exceeds nominal bound by about 5 mrad during the segment | Increasing duration does not necessarily make the coupled pose achievable. Soft simulator limit compliance is distinct from an exact kinematic bound. |
| Timed start 2, frame rotation at decision 5 | EEF target arrives, but finger contacts disappear during the move | Grasp retention cannot be certified by pose IK or EEF arrival. |
| Timed start 2, final placement at decision 24 | Final EEF error about 1.5 mm; eventual tool relation wrong | A reachable target can still be the wrong semantic/geometric target. |

The private diagnosis inspects predefined saved-state intervals and contact geometry;
it does not reconstruct forces or prove causal attribution. Expected finger/object
contacts occur in many segments. A hand/frame contact occurs in the lift preceding
the timed wrist turn. A scene-free kinematic model cannot establish clearance.

## Fixed IK screen

The screen evaluated every one of the 17 waypoints in the predefined ten-command
cohort. Inputs were robot joint positions and policy-requested EEF poses, with the
known Panda/gripper/base model. Four fixed seeds, 150 function evaluations per seed,
1 mm / 0.01 rad pose tolerances and a one-degree joint-bound margin were recorded
before implementation. No thresholds or seeds were tuned.

Fourteen targets have tolerance-passing solutions. Three do not: guarded decision
14's second waypoint, timed decision 19's second waypoint and timed decision 20.
Their best position/orientation residuals are respectively 13.32 mm / 0.242 rad,
9.80 mm / 0.183 rad and 6.90 mm / 0.125 rad. The recovery target at guarded decision
15 passes, as do the final wrong-placement targets. A failed bounded search is not
proof of global unreachability. Nor does a passing search imply dynamic arrival.

The complete screen took 5.56 seconds; per-pose solve p95 was 0.295 seconds. Zero
Astra requests were used. Robot-only FK matches the original environment to below
1e-12 for position and rotation, and compiled joint bounds match exactly.

Attempt 001 is invalid and retained separately: the initial standalone robot export
omitted the parent environment's radians compiler setting. Assigned-q FK matched,
but compiled joint bounds were interpreted as degrees. Its apparent solver failures
are not scientific results. Attempt 002 restores that setting and checks bounds
before solving. This repair changes model fidelity, not the predefined solver gates.

There is also a public-sensor gap: robosuite's raw joint-position observable is
inactive by default, and the current public filter omitted the active sine/cosine
representations. Previous native policies received joint velocity, not joint angle.
Future conditions must both receive genuine encoder positions and the known robot
model. Private joint states in this retrospective diagnosis cannot be silently
treated as prior policy inputs.

## Selected next experiment

Add an optional pose-feasibility query: Astra supplies up to four candidate EEF poses;
the harness returns bounded IK residuals, joint margins and an explicit no-solution
qualification. The query does not move the robot, choose a replacement, cancel a
motion or certify collision/grasp/task success. Astra chooses whether to query and
what to do afterward. Both conditions retain the same waypoint executor and empty
continuation semantics. This tests a communication/planning aid under H4, with robot
feasibility as the revised explanation. It is separate from the earlier arrival or
finger-stop comparisons.

Both conditions receive the same raw joint positions, known kinematic model, libraries
and temporary calculation access. The baseline can calculate from those inputs;
the harness supplies the structured query. Its benefit may be convenience, reduced
policy calculation effort or fewer wasted moves, and it may add calls without helping.
No task improvement is inferred from the retrospective screen.

The [prospective mechanism protocol](mechanism_protocol.json) selects two new matched
starts before implementation or policy evaluation. First verify integration with
paired fixed robot executions: a query must leave physics and subsequent actions
unchanged, with exact input/output logs and known-model boundaries. Then freeze the
implemented sources and byte-identical common policy materials before dispatching
the four scheduled fresh-context Astra episodes. No third or replacement start is
planned. Preserve every result, including non-use of the optional query.

Evidence: [diagnosis](discriminator_result.json),
[calculation verification](calculation_verification.json),
[valid screen](feasibility_attempt_002/result.json),
[invalid attempt](feasibility_attempt_001/invalid_attempt.json).
The original [selection decision](decision.md) remains the prospective discriminator
record. This account selects its feasibility branch after examining the evidence.
