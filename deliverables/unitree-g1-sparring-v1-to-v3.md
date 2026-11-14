# Unitree G1 Sparring in MuJoCo

We built three versions of a live sparring demo with two simulated Unitree G1s, Teal and Amber. The brief called for recognizable punches, kicks and counters, with each fighter reacting to the other. Each finished video contains three full rounds. V1 got live agent control into the ring but struggled with balance. V2 improved posture and made front kicks clearer, while its tactical interface produced repetitive exchanges. V3 gave the agents direct control over individual moves and combinations, then made the scoring visible in the video.

## The three versions

| Version | How fights were controlled | Simulated round length | Finished video | Scored contacts |
| --- | --- | --- | --- | ---: |
| V1 | Teal’s agent fought GGSD in rounds 1 and 2. Both sides had agents in round 3. | 27 s each | [V1 · 1:34](unitree-g1-sparring-v1.mp4) | 46 |
| V2 | Local controllers in round 1. Two agents adjusted tactics in rounds 2 and 3. | 27 s each | [V2 · 1:34](unitree-g1-sparring-v2.mp4) | 17 |
| V3 | Two agents called individual moves and conditional follow-ups in every round. | 24 s, 23 s, 24 s | [V3 · 1:22](unitree-g1-sparring-v3.mp4) | 67 |

Video time includes the title and result cards and reflects each cut’s playback speed. Scored contacts are taken from the rounds in the released videos. The detector and scoring rules changed across versions, so the counts describe the footage under each version’s rules.

## What ran live

MuJoCo simulated both fighters together at 480 Hz. The motor controller updated joint targets at 30 Hz. At a decision boundary, the simulator wrote a JSON observation for each agent due to act, then waited for an action file before advancing. The observations included the opponent’s range and bearing, limb positions and velocities, recent contacts, and score. Agent decisions were made against that evolving state. Pausing the simulation let an agent use more wall-clock time without consuming round time.

The agents worked at the tactical level. Local code converted the chosen moves or preferences into motor targets, tracked the opponent, and handled balance. MuJoCo resolved collisions. The renderer later played back the saved physics states, with a ringside camera, synthesized footsteps and impact sounds, and graphics driven by the logs.

## V1 Learned motor control and live move calls

V1 used the published GGSD Unitree G1 boxing rig and learned motor policy. The first two finished rounds gave Teal a live agent and Amber GGSD’s learned tactics. Both fighters had separate agents in the finale. An agent chose a skill roughly every 0.8–1.0 simulated seconds. Its command could specify a side, target, power and timing, and could request a follow-up if a condition held partway through the window.

The learned policy provided a starting point for locomotion and punching. We added steps to close or change angle, slips, jabs, crosses, hooks, and leg attacks using inverse kinematics, which works backward from a desired hand or foot position to the joint angles. Early bouts sometimes ended on a knockdown after less than five seconds. The release used timed rounds with simulated recovery assistance so the footage could show sustained exchanges.

The user flagged three problems: the stance looked crouched between exchanges, fighters wandered in unstable poses late in the video, and some leg attacks looked like knee touches. Teal also lost the first two rounds by wide margins. In the V1 finale, the robots spent about 14.9 of the 27 simulated seconds at least 0.95 m apart. Over those samples, the mean torso tilt from vertical was about 35° for Teal and 30° for Amber.

## V2 Upright guard and distinct styles

V2 replaced the GGSD motor policy with a task-space controller. It set hand and foot targets, solved the joint angles, and applied equal simulated support at both pelvises. Foot placement, a taller guard, and a kick with a defined chamber, extension and retraction were part of the redesign. Teal was set up to press with straights and front kicks. Amber used a higher guard and looked to slip, move off line, and counter.

In the two agent rounds, each agent updated five preferences every 2.7 simulated seconds: pursuit pressure, kick frequency, defensive tendency, punch target and preferred side. The local controller selected each specific punch, kick or step from live range and limb motion. An agent could favor kicks or aim punches at the body, but it could not directly call a particular kick or time a counter. Each agent submitted ten plans per round.

Using the same 0.95 m separation threshold as V1, average torso tilt was roughly 3–5° for each fighter in V2’s three published rounds. Teal landed a clear extended body kick near 1:29 in the video. The changes fixed much of the stance problem, but the fixed attack rhythms and recurring resets made the exchange feel like dancing. Sixteen of 17 scored contacts were to the body, every scoring kick was a front kick, and Amber scored only once across the two agent rounds.

## V3 Direct exchange control

V3 gave each agent a move command with a strike side, target, pace, delay, power and amount of travel. Each agent could also name a second move and make it conditional on range, an incoming attack, or whether the opener landed, hit the guard, or missed. The simulator checked the condition at the end of the opener. When the commanded exchange ended, that fighter received a fresh observation even if the other fighter was still executing its move.

The following is an actual Teal command from the final round. Teal called a left slip followed by a right jab if it was still within 0.69 m. The jab was aimed at the head, but MuJoCo registered the contact on Amber’s body at 20.63 simulated seconds. The distinction between the requested target and the measured contact is visible in the video.

```json
{
  "turn": 26,
  "move": "slip",
  "side": "left",
  "pace": 0.72,
  "travel": 0.87,
  "follow": {
    "move": "jab",
    "side": "right",
    "target": "head",
    "pace": 0.72,
    "power": 1.15,
    "travel": 1.35
  },
  "when": "close"
}
```

The move set included jabs, crosses, hooks, uppercuts, overhands, four kick types, and defensive moves such as slips, pullbacks and covers. We tuned a separate motion for each strike, added more commitment on head punches, and let the balance controller yield briefly after hard impacts. Both agents still relied on those coded motions and on simulated support. They supplied 193 commands across the finished match. The simulator started 324 moves, including 131 executed follow-ups.

### How the rounds differed

| Round | Video start | What happened | Contacts by target | Contact points, Teal–Amber |
| --- | ---: | --- | --- | ---: |
| 1 | 0:00 | Both fighters worked at kicking distance. Amber attacked the lead leg, then landed a cross to the head and an uppercut to the body around 0:19. | 19 leg, 6 body, 1 head | 4,141.5–7,959.6 |
| 2 | 0:28 | A closer starting distance produced more punching exchanges. Amber’s overhand around 0:45 began a stretch of lead changes. | 3 leg, 10 body, 5 head | 4,542.8–4,933.8 |
| 3 | 0:54 | Amber landed an overhand into an uppercut around 0:58. The round mixed kicks with head and body combinations, including Teal’s late slip-to-jab counter around 1:16. | 8 leg, 11 body, 4 head | 5,117.8–6,368.9 |

Amber won the match 3–0 on contact points. Round 2 was the closest, with 391 points between the fighters. The three bouts differed in starting distance and some controller tuning, so the result is a demonstration of the system in use with those settings.

## Scoring and presentation

V1 used the closing speed of a limb at a qualifying contact to award points. V2 and V3 used normal impulse, the force perpendicular to the contact surface accumulated over the physics steps. In V3, the scoring logic checks the active strike and striking limb, the body part hit, a minimum impulse of 1.25 N·s and a minimum peak normal force of 60 N. It caps the base award and applies a target multiplier. Contacts with the opponent’s gloves, wrists or elbows can inform a follow-up, but they do not score.

V3 displays the current calls at the top of the frame and shows the move, measured target and points at the bottom when a hit scores. The round timer, cumulative points, rounds won and result cards explain how a winner was decided. The display and audio use the contact logs. The final cut contains whole rounds, with chapter markers at each round boundary.

## Project files and scope

- [V1 simulator and agent interface](../fight.py) and [added motor skills](../skills.py)
- [V2 local fighter controller and contact meter](../kickboxing.py)
- [V3 exchange commands and follow-up logic](../exchange.py)
- [Arena](../arena.py), [video renderer](../render.py), [round assembly](../assemble.py), and [run instructions](../README.md)

The released rounds map to `runs/main-01`, `runs/main-04` and `runs/final-duel` for V1, `runs/kick-v8-24`, `runs/v2-live` and `runs/v2-live3` for V2, and `runs/v3-live1` through `runs/v3-live3` for V3. Each folder contains the round settings, results, impacts and saved simulation states. In V3, `commands.jsonl` pairs each agent’s observation with its reply, `decisions.jsonl` records the moves actually started, and `guard-contacts.json` tracks contact with the guard.

The project borrowed its G1 model from GGSD, with the source revision pinned in [the asset fetcher](../fetch_assets.py). We considered HoloBoxing. Its published competition rules score hand contacts to the head and torso. The kickboxing brief called for kicks and leg targets, which we implemented in the custom controller and scoring code. [HoloBoxing rules](https://github.com/HorizonRobotics/HoloMotion/blob/master/holoboxing/README.md#match-rules)

V3 demonstrates live tactical control of two assisted robots in simulation. The balance forces and timed round rules are part of the setup. The motion library still limits what each agent can invent, and some guard resets and close exchanges look mechanical. The videos and logs document what happened under this setup and provide a basis for inspecting individual exchanges.
