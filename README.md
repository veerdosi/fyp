# Foundation-model robot communication experiments

This FYP studies which information and action interfaces help a foundation model
control a robot, and what observed failures explain their contribution. Sol owns
research and implementation; fresh GPT-6 Astra contexts at medium effort make
robot decisions. See [AGENTS.md](AGENTS.md) for experiment rules.

## Read first

- [Research plan](docs/research_plan.md): current question, next decision and experiment design.
- [Results account](docs/empirical_account.md): completed findings and their limits.
- [Interface reference](docs/communication_interface.md): sensors, commands, controller and policy boundary.
- [Literature review](docs/literature_review.md): relevant prior work and novelty limits.
- [Original objective](docs/goal_objective.md): the user's project scope and completion criteria.

Current direction, 2026-10-14: choose a new task and a diagnostic comparison that
separates feature estimation, conversion into robot motion, physical execution and
completion judgment. The [16-episode reason audit](studies/cross_episode_failure_audit/account.md)
is the evidence behind this decision. Collision/contact prototypes are not the
default next experiment. Two matched starts are the default; no new batch is scheduled.

## Repository layout

| Location | Contents |
| --- | --- |
| `src/fyp/` | Simulator adapters and shared executor/sensor implementation |
| `scripts/` | Setup, episode serving, policy handoff, recording and analysis |
| `studies/` | Paired-study evidence and compact results/protocols for closed prerequisite screens |
| `runs/` | Original policy inputs/outputs, public sensors, actions, trajectories and outcomes |
| `docs/` | Current project references; detailed evidence stays with its study |

## Setup and smoke run

Requires Python 3.11 and `uv`. From the repository root:

```sh
sh scripts/setup/setup.sh
.venv/bin/python scripts/setup/probe.py
.venv/bin/python scripts/episodes/episode.py smoke --run /tmp/fyp-tool-hang-smoke --suite robosuite --task ToolHang --seed 300
.venv/bin/python scripts/episodes/episode.py replay --run /tmp/fyp-tool-hang-smoke
```

Always use a fresh output directory. Dependencies are recorded in `requirements.in` and `requirements.lock`. The active
backend is native robosuite/MuJoCo; LIBERO assets, configuration and setup have been
removed. The runtime was exercised on macOS arm64 with Python 3.11.4, MuJoCo 3.2.7
and robosuite 1.4.1. ToolHang/NutAssembly use the existing Panda OSC_POSE.

## Replay and analyze existing evidence

Replay uses recorded actions and requires no Astra calls. For strict public-sensor
checks, use the matching study replay helper:

```sh
.venv/bin/python studies/tool_hang_v2/replay.py --run runs/th_v2_s02_guard
.venv/bin/python studies/pose_feasibility_v1/replay.py --run runs/pf_v1_s01_waypoints_corrected
.venv/bin/python studies/cross_episode_failure_audit/analyze.py
```

The [results account](docs/empirical_account.md) links every study's reproducibility
instructions. Videos remain local and are ignored by Git; recorded actions,
sensors and state trajectories provide reproducible evidence. Model decisions
cannot be reproduced simply by replaying physics.

## New robot-policy episodes

A diagnostic infrastructure example, using a fresh directory:

```sh
.venv/bin/python scripts/episodes/episode.py serve --run runs/new_tool_hang_pilot --suite robosuite --task ToolHang --seed 400 --condition direct_waypoints
.venv/bin/python scripts/policy/prepare_policy.py runs/new_tool_hang_pilot
```

The server binds to `127.0.0.1:8765` and pauses physics between commands. The saved
prompt goes verbatim to a fresh Astra robot-policy context. `scripts/policy/relay_policy.py`
transports that agent's exact command from its native session; it is an operator
adapter, not a standalone model API. `scripts/policy/policy_calc.py` logs permitted
in-episode calculations. Follow the [interface reference](docs/communication_interface.md)
and routing skill for model selection, tools and audits.

These commands do not enroll a new evaluation. Before a comparison, freeze its
question, conditions, task, starts and budgets in a new protocol. Existing launchers
check frozen source/material hashes; never reuse a completed scheduled episode ID.

Historical protocols and saved prompts retain their original paths and source
hashes. To rerun a frozen historical setup, use its recorded Git revision; do not
rewrite the protocol to accept current code. Current native action replay uses the
helpers above. The retired microwave records require their original LIBERO revision
and dependencies. See [script groups](scripts/README.md) for current entry points.
