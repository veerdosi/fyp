# TAPNext++ probe stopped after research-priority review

The probe was stopped after the user questioned whether this tracker step deserved
more time. Sol recommended moving on and terminated the worker. This is a priority
decision, not a technical or accuracy failure. No full accuracy audit is scheduled.

The official 512-resolution checkpoint loaded on MPS and produced 34 chronological
fixed-camera outputs, each checked against its current input frame and recurrent
state step. The second camera was not reached, the 65-frame-per-camera probe was
incomplete and no geometry was scored. This establishes that an initial segment
runs locally; it establishes neither complete feasibility nor measurement accuracy.
The original protocol, outputs, progress, dependencies and source/checkpoint hashes
are retained. The process ended by SIGTERM after 120.23 host seconds. Zero Astra
requests were used. See [operator stop](operator_stop.json),
[protocol](probe_protocol.json) and [partial outputs](probe_mps/outputs.jsonl).

The tracker has a specific prospective role: improve correspondence and visibility.
But the preceding depth screen also failed source support/coverage, and robot traces
show wrong object relations even after accurate EEF arrival. A correspondence
improvement alone would not settle those problems. Given the user's priority for
fast mechanism iteration, a full development audit has less immediate value than a
new communication/embodiment question. The earlier tracker decision remains frozen;
this [subsequent decision](next_test.md) supersedes its execution schedule.

The [official implementation](https://github.com/google-deepmind/tapnet/tree/730cda1c730877cfedbe01bf87fb1cadb78a565d/tapnet/tapnextpp/votsp2026)
was used without changing model code: float32, 512 input, official visibility logit
threshold and 64 local support points per real query. The public archive's RGB was
converted to the wrapper's BGR convention. Model coordinate space remains 256;
support radius is scaled from the 512 input space. No future frames, private geometry,
silent CPU fallback or accuracy-based tuning were used.

To inspect retained outputs, read the JSONL and logs. Re-executing the probe requires
a new recorded attempt directory: the script deliberately refuses to overwrite
`probe_mps`. Clone the pinned official source into `vendor/tapnet`, obtain the public
checkpoint at the URL in the protocol, and install the dependency versions recorded
there. No further run is necessary for the current decision.
