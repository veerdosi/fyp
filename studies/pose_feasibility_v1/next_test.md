# Next necessary test: distinguish placement errors before another interface

This decision follows the completed feasibility comparison and precedes any new
implementation. Both second-start policies acquired the objects but failed their
placement relations. Their logged rotations were computed from selected visible
points; repeated insertion contact and changing geometry followed. Another grasp
interruption or pose-query variant does not address that evidence.

Use every calculation in the corrected four-episode batch: three in
`pf_v1_s02_preview` and two in `pf_v1_s02_waypoints`; the first pair used none.
For each, inspect the exact public input provenance, arithmetic/output, next
motion's requested and reached poses, public images and sensing updates. Do not
select only calculations with favorable attachment or clear visibility. Retain
ambiguous point identity or incomplete provenance as unknown.

Compare each following motion's recorded object-to-gripper transform at its first
and last step, and through the segment. Use private object geometry only for
offline diagnosis, never a future policy or executor input. Distinguish a measured
change from a verified rigid attachment. Use the already declared 3 mm / 0.03 rad
robot exit tolerances as descriptive reference thresholds for transform changes;
they are not a new success gate or grasp certificate.

Record whether the selected reference is ambiguous/background, whether the
calculation uses a stale object-to-hand relation, whether contact prevents the
requested robot motion, or whether robot arrival still yields wrong placement.
Short command reasons supply stated expectations, not hidden reasoning or proof
of causal reliance. Multiple causes may remain unresolved in one motion.

Decision: if arithmetic/provenance is the identifiable bottleneck, justify a
specific calculation or representation intervention. If attachment/reference
geometry changes, require a demonstrably usable public remeasurement route before
object-relative correction. If contact prevents otherwise sensible motion,
prioritize trajectory/interaction handling. If no observable input can support
the intended precision, select a different suitable task rather than adding an
oracle relation check or repeatedly auditing trackers. No positive result is
promised, and no new robot batch is scheduled at this stage.

This screen requires zero new Astra calls and no new start. Any subsequent robot
comparison must have its own prospective prediction, two matched starts, equal
sensor/calculation access and a frozen controller/interface. No implementation or
policy launch precedes this discriminator's decision.
