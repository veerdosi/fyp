# Placement-error discriminator

All five preregistered calculation cases were retained, with zero new Astra calls.
Their source hashes and stdout/stderr reproduce exactly. Recorded object-to-hand
transforms were independently recomputed from absolute object and robot poses and
agree with the pinned native relative observations within 1e-6. The complete
per-step changes and motion exits are in [results.json](results.json).

| Case | Following decision | Maximum object-to-hand position change | Maximum rotation change | Interpretation |
| --- | --- | --- | --- | --- |
| Preview / rotation correction | 10 | 5.01 mm | 0.08884 rad | Frame geometry changes during the correction/contact sequence |
| Preview / axes inspection | 14 | 26.73 mm | 0.04560 rad | The following command intentionally regrasped; this is not proof of stale arithmetic |
| Preview / hook alignment | 22 | 1.14 mm | 0.01564 rad | Attachment is comparatively stable during this approach; later placement still fails |
| Baseline / frame rotation | 9 | 2.54 mm | 0.02082 rad | Initial rotation/transport has stable relative geometry; later insertion stalls |
| Baseline / tool rotation | 18 | 1.84 mm | 0.02064 rad | Initial tool approach is comparatively stable; later threading/release fails |

The 3 mm / 0.03 rad reference thresholds are inherited descriptive tolerances,
not a newly tuned gate, grasp certificate or task-success criterion. This tests
only the immediately following motion. It does not certify attachment through
later insertion and release, nor diagnose the identity of every selected pixel.

The public provenance inspection finds measured EEF quaternions and selected
surface coordinates in all five programs. Baseline frame rotation uses the
recorded frame-end query and measured grip pose; baseline tool rotation uses two
ring-rim points and its measured grip pose. Its selected ring height is about
3.003 mm below their mean surface height. That is an undocumented geometric
offset, not an identified arithmetic error. Preview hook alignment combines
selected visible rim coordinates and two hook-lip points. Their interpretation
as a hole center/axis remains an estimate, not an identity or geometry certificate.
The other two preview calculations inspect or modify measured hand orientation.
Reproducing the numbers does not establish that the model selected the right
geometric relation.

The evidence argues against selecting a simple arithmetic compiler as a
correctness remedy: no arithmetic execution fault is identified, and three
approaches retain relative geometry within the descriptive reference tolerances
before failing later. Frame corrections can change attachment, but this is not
a universal explanation either. Subsequent insertion and clearance motions are
contact-limited: baseline frame descent ends 50.44 and 36.58 mm short; preview
frame descents end 17.42 and 9.93 mm short. Repeated reached release poses also
fail to establish the desired final relation. The public reasons and images
already show these events; private geometry supplies precise offline diagnosis.

The earlier contact-feedback proposal was superseded by the broader cross-episode
audit. The current allocation is in [the research plan](../../docs/research_plan.md);
no wrist-screen prototype or new policy batch has been run. These results remain
development evidence separating arithmetic, attachment and physical interaction.

Reproduce with `.venv/bin/python studies/placement_error_discriminator/analyze.py`.
This is a development discriminator on the completed batch, not held-out policy
evidence for a correction mechanism. Private poses remain excluded from future
policy/executor inputs. The broader FYP remains active.
