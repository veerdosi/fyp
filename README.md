# Foundation-model robot communication experiments

This project tests which communication mechanisms help a slow foundation model control a robot. Development and analysis use Sol; robot decisions use fresh GPT-6 Astra episode contexts at medium reasoning effort. The interface is to be chosen from direct-control failures. No paired efficacy result exists yet.

The first environment is the standard LIBERO-10 task `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it`, with the standard Panda robot and OSC_POSE controller. Simulator-only object state and reward are excluded from robot decisions. See [sensor audit](docs/sensor_audit.md), [research plan](docs/research_plan.md), and [experiment status](docs/experiment_status.md).

## Run on this Mac

Install `uv` and Python 3.11, then:

```sh
sh scripts/setup.sh
.venv/bin/python scripts/probe.py
.venv/bin/python scripts/episode.py smoke --run runs/new_smoke
.venv/bin/python scripts/episode.py replay --run runs/new_smoke
```

The pinned LIBERO checkout is installed in `vendor/LIBERO`; the project-local config is in `.libero`. Training code and pretrained policies are not required. Dependencies are pinned in `requirements.lock`; `requirements.in` records the direct dependencies. The runtime has been tested on macOS arm64 with Python 3.11.4, MuJoCo 3.2.7 and robosuite 1.4.1. It uses offscreen rendering without a desktop MuJoCo viewer.

## Run a robot-policy episode

```sh
.venv/bin/python scripts/episode.py serve --run runs/new_pilot --state-index 0 --seed 100 --condition direct_waypoints
```

The server binds only to `127.0.0.1:8765`. It pauses physics while waiting for a command. A policy decision is a JSON `sense`, `move`, or `finish` command. See the logged initial prompt of the first pilot for the complete schema, budgets, allowed sensors, and tool restrictions. `scripts/send_command.py request.json` sends a logged envelope with `command` and `policy` fields to the server. The policy metadata records exact model, effort, input and raw response.

The first pilot is called through the Codex collaboration interface; `scripts/relay_policy.py` can copy a matching returned robot decision from that root chat's local rollout into a recorded request and execute it. It exports only messages from the selected robot agent. It requires that exact session file and is an experiment-operator adapter, not a standalone model API. Model access remains a separate requirement for new policy runs. Deterministic action replay requires no model access.

Each run saves config, initial state, robot observations, model inputs/outputs, sensor queries, native actions, diagnostics, an action/state trajectory, video, and outcome. Raw videos are retained locally and ignored by Git. Replay compares every saved state and the final score; it does not ask a model to regenerate its decisions.

Fresh episodes now begin with a fixed 20-step open-gripper settling period. The original smoke run and first diagnostic pilot began immediately after loading the benchmark state. Do not mix those starts into a settled paired comparison. Verification and pilots are recorded separately from future held-out evaluation.
