# Calculation runtime lesson

On this Mac, importing MuJoCo invokes `sysctl`. The policy calculation wrapper's
restricted PATH omitted `/usr/sbin`, so a development-process import did not establish
that the permitted in-episode helper would work. Add `/usr/sbin:/sbin` to the common
wrapper PATH. Before a policy batch, execute each new allowed helper/library through
the actual logging wrapper in both conditions using public-sensor fixtures.

The corrected wrapper produced identical successful IK outputs in both fixtures.
The user requested removal of the broken episode records; keep this implementation
lesson and verification, without its outcome, usage or trace in the study results.
