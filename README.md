# Foundation-model robot communication experiments

This project tests which communication mechanisms help a slow foundation model control a robot. Development and analysis use Sol; robot decisions use fresh GPT-6 Astra episode contexts at medium reasoning effort. Two ToolHang pilots support testing measured waypoint transitions and observation handoff. The completed six-episode comparison found 0/2 full native successes in each condition. Robot-arrival gating did not establish a task-success or successful-completion efficiency benefit; see [the empirical account](docs/empirical_account.md).

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

The server binds only to `127.0.0.1:8765`. It pauses physics while waiting for a command. A policy decision is a JSON `sense`, `move`, or `finish` command. Generate a self-contained prompt for a fresh episode with `.venv/bin/python scripts/prepare_policy.py runs/new_pilot`; it includes the schema, budgets, sensors and matched temporary-calculation access. `scripts/send_command.py request.json` sends a logged envelope with `command` and `policy` fields to the server. The policy metadata records exact model, effort, input and raw response.

The first pilot is called through the Codex collaboration interface; `scripts/relay_policy.py` can copy a matching returned robot decision from that root chat's local rollout into a recorded request and execute it. It exports only messages from the selected robot agent. It requires that exact session file and is an experiment-operator adapter, not a standalone model API. Model access remains a separate requirement for new policy runs. Deterministic action replay requires no model access.

Each run saves config, initial state, robot observations, model inputs/outputs, sensor queries, native actions, diagnostics, an action/state trajectory, video, and outcome. Raw videos are retained locally and ignored by Git. Replay compares every saved state and the final score; it does not ask a model to regenerate its decisions.

Fresh episodes now begin with a fixed 20-step open-gripper settling period. The original smoke run and first diagnostic pilot began immediately after loading the benchmark state. Do not mix those starts into a settled paired comparison. Verification and pilots are recorded separately from future held-out evaluation.

## Existing MuJoCo precision candidates

Native robosuite tasks reuse the same direct-control executor and sensor boundary:

```sh
.venv/bin/python scripts/episode.py smoke --run runs/new_tool_hang_smoke --suite robosuite --task ToolHang --seed 300
.venv/bin/python scripts/episode.py replay --run runs/new_tool_hang_smoke
.venv/bin/python scripts/episode.py serve --run runs/new_tool_hang_pilot --suite robosuite --task ToolHang --seed 400 --condition direct_waypoints
.venv/bin/python scripts/prepare_policy.py runs/new_tool_hang_pilot
```

`NutAssemblySquare` and `NutAssemblyRound` are also supported. These use existing geometry, placement and scoring; no Isaac Sim assets or custom puzzle port are required. ToolHang was selected from one successful and one unsuccessful direct pilot. The [selection record](docs/task_selection.md) explains the mechanism and its limits.

For a completed run, `.venv/bin/python scripts/summarize_episode.py runs/RUN_NAME` records offline waypoint tracking errors, raw wrist loads and private goal timing. These diagnostics are excluded from policy inputs. `scripts/export_policy_usage.py` exports actual inference requests, tokens and an API-equivalent cost estimate; `scripts/export_policy_tools.py` exports exact tool invocations for manual boundary review. Both require the episode agent's native session path. Calculation code and outputs are saved separately by `scripts/policy_calc.py`.

The experiments may support higher success, fewer calls, faster verified completion, lower cost, or no improvement; no particular benefit is assumed. Simulated control time, native policy-turn time, response delivery and total elapsed are distinct. Retries fit within 30 robot decisions and 120 simulated seconds, with no separate retry count. The [frozen protocol](studies/tool_hang_v1/protocol.md) records two paired starts, timed/deadline/early-arrival conditions, primary success, all resource outcomes and analysis rules.

The completed study was launched through `scripts/start_study_episode.py`. New evaluations require a separately frozen protocol and fresh episode IDs; the launcher accepts `--protocol PATH`. Generate each episode's full fresh-context prompt with `scripts/prepare_policy.py`. Frozen source and policy material hashes are checked before starting. After recording, auditing and replaying each run, `.venv/bin/python scripts/analyze_study.py` reports paired results and flags missing evidence. Operator access to Astra remains required; action replay is independent of model access.
