# Point feedback needs a reliable measurement

The frozen local optical-flow prototype failed the measurement gate. It should not drive an object-feedback executor. This finding narrows a candidate implementation; it does not reject object feedback in general or resolve the wider effect of arrival gating.

The six ToolHang policy runs motivate this question because gripper arrival coexisted with object slip, shallow seating, displacement during withdrawal and incorrect completion judgments. A point measurement could expose some object motion that robot state misses. It cannot choose the correct hole, repair a grasp or infer hidden contact geometry. The audit therefore tests measurement feasibility before another costly policy comparison.

## Complete development cohort

All 212 recorded pixel selections were retained, covering 35 following-motion streams from both already observed starts. There were 22,739 point/frame outputs and zero new model requests. These are correlated observations, not 22,739 robot trials or held-out results. Every original outcome remains unchanged.

The estimator received only RGB, metric depth, public calibration and selected pixels. Its parameters were frozen before scoring and were not revised from the result. Private image-time ray/body references supplied scoring only. A geometric surface match does not establish the semantic correctness of a query. Reference geometry was available for 171 queries; 41 queries / 4,206 samples remain reference-unknown, not automatically wrong selections. They were retained and excluded only from metrics requiring a known geometric reference.

The audit replayed all 10,878 native actions and reproduced every simulator state exactly. All 49 queried camera snapshots reproduced RGB, depth and public calibration exactly. Forced state restoration had shifted native sensor sampling in earlier reconstruction attempts; those drivers and failures remain preserved. Matching the original initialization resolved that audit artifact. With the final read-only reference wrapper, measured image age was zero and image-time/current-step errors agreed. Initial public unprojection differed from image-time reference by at most 2.36e-16 m. This cohort provides no evidence that calibration timing caused the tracker failure or the v1 task failures.

## Frozen gate results

| Group | Visible coverage | Accepted error p95 | Occluded points accepted |
| --- | ---: | ---: | ---: |
| Required | >=80% | <=3 mm | <=5% |
| Overall | 63.1% | 9.28 mm | 25.9% |
| Fixed camera | 75.8% | 12.52 mm | 26.5% |
| Wrist camera | 34.0% | 6.35 mm | 21.6% |
| Translation | 60.9% | 20.67 mm | 69.4% |
| Includes rotation | 63.7% | 9.27 mm | 18.5% |
| Start 1 | 68.3% | 9.27 mm | 41.7% |
| Start 2 | 59.4% | 10.35 mm | 14.8% |

All requested categories were represented and failed the gate. Overall, 10,090 of 15,998 reference-visible samples were accepted; 1,573 of those accepted samples exceeded 3 mm. The estimator accepted 657 of 2,535 reference-occluded samples. Its accepted visible median error was only 0.093 mm, so a typical-error figure alone would hide the tails and loss failures.

Private body groups help diagnose this mixture. Visible stand points had 93.6% coverage and 2.56 mm p95 error, but 82.6% false-valid acceptance when occluded. Frame points had 53.6% coverage and 21.04 mm p95 error. Neither supports deploying this estimator. A diagnostic frame query in the second deadline trace exceeded 3 mm for 115 of 145 following steps, reaching 28.2 mm error, while its median forward/backward residual on those bad samples was only 0.000217 pixels. Local round-trip consistency did not certify the identity of the transported surface point. This ranking is diagnosis from the full cohort, not a replacement evaluation subset.

## Revised implication

Robot arrival and local image consistency are both incomplete certificates for an intended object relation. The next measurement candidate needs an explicit correspondence/loss estimate that survives these thin surfaces and occlusions. Preserve this failed prototype without threshold tuning. A stronger generic tracker can be considered, but its causal availability and runtime must be checked on this Mac before another full cohort audit or any Astra comparison. Accuracy on development streams would still require a separate frozen robot experiment to establish a harness benefit.

See [the full metrics](results.json), [completeness checks](verification.json), [diagnostic cases](failure_cases.json) and [gate figure](measurement_gates.svg). Reproduce with the commands in [README.md](README.md).
