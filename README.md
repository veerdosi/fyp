# Unitree G1 sparring in MuJoCo

Two simulated Unitree G1s share a MuJoCo ring. V2 uses `kickboxing.py`: Teal presses with straight punches and front kicks; Amber has a higher guard and looks for slips and counterpunches. Each fighter chooses independently using live range, limb motion, and its recent actions. Inverse kinematics updates limb targets at 30 Hz and MuJoCo steps at 480 Hz. Both fighters receive simulated balance and locomotion assistance at the pelvis. A hit is recorded only when the striking glove or foot contacts a valid opponent target during an attack and exceeds the force and impulse thresholds.

The original V1 system is still available in `fight.py`. An external agent selects skills above GGSD's motor network, which runs at 30 Hz. The opposing fighter can use a separate agent or GGSD's learned tactics. Added moves use joint targets and inverse kinematics, and a conditional follow-up can change the move halfway through a decision window.

The rig and learned weights come from the authors' [GGSD demo](https://ggsd-demo.github.io/?game=g1_boxing). The source revision is pinned in `fetch_assets.py`.

## Run

Use Python 3.12 and FFmpeg.

```sh
uv venv --python 3.12
uv pip install -r requirements.txt
.venv/bin/python fetch_assets.py
.venv/bin/python kickboxing.py runs/local --seconds 27 --seed 91
.venv/bin/python render.py runs/local runs/local/demo.mp4
```

Add `--bridge runs/local-bridge --interval 2.7` to let two external agents adjust tactics. The simulator publishes `observe-0.json` and `observe-1.json` at each boundary and resumes when both agents submit a plan. Each agent atomically writes `action-<side>-<turn>.json`, padding the turn to three digits. The simulator records both observations and submitted plans in `plans.jsonl`. A plan has this format:

```json
{"turn":0,"pressure":0.7,"kick":0.6,"defense":0.3,"target":"auto","lead":"auto"}
```

The three weights range from zero to one. Target can be `auto`, `head`, or `body`; lead can be `auto`, `left`, or `right`. The local controllers continue choosing and aiming individual strikes and steps between agent decisions.

V3 uses `.venv/bin/python exchange.py runs/bout runs/bout-bridge --seconds 24`. The same per-fighter file interface now accepts an individual move and an optional conditional follow-up. Each fighter gets a fresh observation as soon as its last command completes. The simulator logs the observation and submitted command in `commands.jsonl`, and the moves that actually ran in `decisions.jsonl`.

```json
{"turn":0,"move":"advance","travel":1.1,"follow":{"move":"hook","side":"right","target":"head","pace":0.9},"when":"close"}
```

The command accepts side, target, pace, delay, power and travel. Follow-up conditions include distance, an incoming strike, and whether the first strike landed, hit a guard, or missed. The task-space controller aims and tracks the commanded move while both robots receive simulated balance and locomotion assistance.

For the original system, run `.venv/bin/python fight.py runs/legacy --agents 0 --endurance --seconds 27 --window 24`. With `--agents 1` or `--agents 2`, `fight.py` instead waits for commands such as `{"turn":0,"move":"advance"}`. It lists the move and parameter ranges.

Each completed run saves the decision log, impact log, result and sampled MuJoCo poses. The renderer can recreate a video from those poses with no policy connection.

Use `python assemble.py output.mp4 round-1.mp4 round-2.mp4 round-3.mp4` to join rounds rendered with the same resolution, frame rate and codec. The combined file adds one chapter per round.

An interrupted live run can resume with `fight.py runs/<name> --resume`. The simulator reconstructs the state from its saved decisions, checks the observations against the log, and resumes requesting live actions at the first missing turn.
