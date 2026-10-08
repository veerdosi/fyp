# Next necessary test: can uncertainty make surface feedback usable?

Recorded after all four v2 outcomes and replay/geometry audits, before implementing
or scoring the next estimator. The clean pair favors guarded completion, and the
two stops correctly invalidated empty continuations. Retain that narrow mechanism.
Do not claim it repaired tool/hook geometry or established faster completion.

The repeated unresolved failure is an object relation that the policy describes as
correct while geometry is wrong. The latest timed run contacts the frame's grip
section and table rather than the horizontal hook; both earlier timed baselines also
failed seating. Non-arrival and wrist feasibility contribute, but later EEF arrival
does not verify the selected surface relation. The successful guarded recovery used
a new measured ring/tip alignment, although that measurement's causal contribution
is not isolated. This motivates testing a different measurement/control boundary,
rather than another finger or arrival guard.

The cheapest discriminating test is one fixed public-depth/uncertainty screen using
the retained CoTracker predictions. Its previous metre-scale depth errors sometimes
coincided with subpixel correspondence; its visibility flag also accepted occluded
points. A new tracker alone would not establish metric accuracy. This screen asks
whether local support, discontinuity rejection, temporal plausibility and independent
camera depth consistency can meet the existing measurement gates while preserving
coverage. It does not presume H1 is the answer.

Use the same complete development cohort: 212 original queries, 35 streams, 2757
causal endpoints and the 22739-frame availability ledger. Reuse the frozen 2D
predictions and model-visible flags without another tracker inference. Reconstruct
the original public sensor streams exactly; private body-local references score
accuracy/visibility only. No private identity establishes a cross-camera match.
Keep all unknown references, rejected endpoints and between-update unavailability.
Do not use future frames, interpolate measurements or silently replace streams.

Freeze one primary estimator before scoring:

1. Require the original model-visible flag and finite in-image public depth.
2. Examine the current 3x3 depth neighborhood. Require at least five finite depths
   within 3 mm of their median and a complete patch range no greater than 20 mm.
   Unproject the median depth at the original fractional tracked pixel. Reject
   insufficient support or a discontinuity; do not relocate the point by private
   geometry or select a foreground component retrospectively.
3. Bound change from the last accepted public world point by 1 m/s times elapsed
   simulated time plus 10 mm. Initialize from the original public query. This is
   a conservative plausibility assumption, not an identity certificate; do not
   advance the reference on rejection. Report this assumption and every rejection.
4. Project that candidate into the other camera using current public calibration.
   A finite other-camera ray with depth within 5 mm corroborates it. If the ray's
   observed surface is farther by more than 5 mm, reject the inconsistent candidate.
   If nearer, mark the other view occluded; if outside view or invalid, mark it
   unavailable. Neither occlusion nor unavailable corroboration proves source loss:
   allow the otherwise supported source estimate, with that uncertainty explicitly
   logged. Report corroborated and single-view results separately.

Also report two predefined diagnostic controls, using the exact same predictions:
the unchanged nearest-depth baseline and local support/median alone. They separate
local association from the additional temporal/camera checks. These are development
measurement controls, not new robot-policy conditions or successive tuned candidates.

Keep gates unchanged: visible coverage at least 80%, accepted visible world-error
p95 at most 3 mm and occluded false-valid rate at most 5%, overall and in each camera
and each observed starting state. Report all three together, rejection reasons,
unknown references, causal availability, runtime and the same-sample controls. Do
not select a passing subgroup, change thresholds after scoring or reject everything
and call it reliable. A passing development screen is necessary, not sufficient,
for a held-out H1 policy comparison.

The result must change the next decision:

- If all gates pass, define and verify a bounded object-relative correction command
  with explicit unavailable/lost handoff. Then prerecord a substantial H1 comparison
  on two new matched starts against credible waypoint replanning, with identical
  sensors, calculations and controller. Select the measurable relation and failure
  prediction before implementation; do not retrofit v2 into that experiment.
- If metric depth improves but correspondence/occlusion remains the limiting gap,
  screen one fixed official TAPNext++ configuration on this cohort with the same
  depth policy. Verify Mac feasibility and causal frame access first. Preserve the
  failed CoTracker and depth results; no sequence of alternative trackers or tuning.
- If ambiguity rejection destroys coverage, or no usable precision/loss measurement
  emerges after this screen and one justified tracker screen, retire this surface
  route for the iteration. Select a different trace-supported representation or
  embodiment/feasibility question before another costly policy batch. A tracker
  cannot fix wrong semantic target selection or whole-arm collisions by itself.

No new Astra calls are needed for this screen. Astra remains required for the
subsequent paired policy test once there is a valid interface and frozen prediction.
There is no third v2 start and no additional guard variation. The existing paired
result, its confound and uncertainty remain unchanged.
