# Move to a different communication mechanism

Recorded after the partial feasibility probe and the user's request to consider
moving on. Supersedes the full tracker-screen schedule in the frozen depth decision;
it does not alter the depth results or classify the interrupted probe as failed.

Retire tracked-surface correction for this iteration. H1 remains open; the tested
local-flow, CoTracker/depth and uncertainty configurations have not supplied usable
precision feedback. Preserve the successful empty-continuation invalidation behavior
and its uncertain task effect, without another guard variant or additional v2 state.

The next necessary design test is a comparison of command representations tied to
the recorded rotation/placement failures. The candidate is bounded geometric
delegation: Astra declares a rigid-motion intent and an anchor/pivot from public
measurements; the executor compiles the coupled EEF trajectory. This targets repeated
manual translation/rotation bookkeeping and the gap between a requested robot pose
and intended object motion. It uses current robot kinematics and a policy-declared
rigid relation, without depending on an online object tracker. Astra continues to
select the object, grasp, anchor, destination and recovery. Rigid attachment is an
assumption that must be explicit, not a success certificate.

Before implementing an executor, inspect the actual public calculations and commands
at the failed and successful rotation/placement phases. Establish whether the model
is making transform/trajectory errors this representation could change, or whether
the target relation is already wrong or the arm cannot realize it. Use the existing
replay and geometry records; no new Astra calls are needed for this selection test.
Record a decision table separating correspondence/depth, geometric bookkeeping,
target identity and controller/whole-arm feasibility. A cause unsupported by these
traces must not be used to justify the new command.

If geometric coupling is supported, freeze one explicit prediction and a bounded
command before implementation: retain the same OSC controller, public sensors,
calculation access and budgets against credible direct waypoints. Verify the
primitive on fixed recorded fixtures, then run two new matched Astra starts. Report
full task success as well as the predicted phase error, actual model calls and all
timing/cost; failed runs do not establish completion efficiency.

If the intended geometry is correct but motion is infeasible, choose a robot
feasibility representation instead before implementation. If wrong semantic target
identity dominates, choose explicit relation representation/observation instead.
Do not launch a policy batch until this discriminator selects a mechanism and its
failure criterion is recorded. This selection is a short gate to the next substantive
experiment, not a new tracker search or threshold sweep.
