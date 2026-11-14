# Unitree G1 Sparring V2

Each round contains 27 continuous seconds of live MuJoCo simulation. The render plays the simulation at 0.91× speed and adds a short title and round results. Both robots use the same simulated balance and locomotion assistance.

| Round | Run folder | Tactical control | Contact score, Teal–Amber |
| --- | --- | --- | --- |
| 1 | `runs/kick-v8-24` | Independent local pressure and counter controllers | 2,128.7–1,003.9 |
| 2 | `runs/v2-live` | Two agents adjusted tactics for the local controllers | 722.9–0 |
| 3 | `runs/v2-live3` | Two agents adjusted tactics for the local controllers | 2,490.5–950 |

In rounds 2 and 3, each model submitted ten plans based on its own live observations, one every 2.7 simulated seconds. The local controllers continued choosing and aiming strikes between plans. The run folders contain sampled physics states, tactical decisions, measured contact impulses, and final scores. The corresponding `-bridge` folders contain the external action files.
