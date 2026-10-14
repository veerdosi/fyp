# Script entry points

Run scripts from the repository root with `.venv/bin/python`; setup uses `sh`.

| Folder | Purpose | Main entry points |
| --- | --- | --- |
| `setup/` | Dependency installation and native sensor probe | `setup.sh`, `probe.py` |
| `episodes/` | Native episode serving, frozen-study launch and command transport | `episode.py`, `start_*_episode.py`, `send_command.py` |
| `policy/` | Saved policy prompts, handoffs, exact decision relay and logged calculations | `prepare_policy.py`, `prepare_*_handoff.py`, `relay_policy.py`, `policy_calc.py` |
| `analysis/` | Recorded episode summaries and native usage/tool exports | `summarize_episode.py`, `export_policy_usage.py`, `export_policy_tools.py`, `analyze_study.py` |
| `verification/` | Consequential executor semantics/duration check | `verify_phase_execution.py`, `verify_budget_closure.py` |

Study-specific analysis and replay stay in their study folders. Setup/probes and
verification do not call Astra. Only actual policy episodes use fresh Astra medium
contexts. Sensor probe output defaults to a temporary folder outside the repository.

Current paths differ from frozen historical protocols. Keep their original hashes
and records intact; use their recorded Git revision to rerun a historical setup.
New evaluation protocols must freeze the current source inventory and policy material.

Original policy traces stay under `runs/`. Temporary diagnostic, verification and
smoke run folders have been removed. Their distinct results remain in
[one verification summary](../studies/tool_hang_v1/verification_summary.json).
Use fresh temporary output folders when regenerating checks; do not commit duplicate
fixtures by default. Retired measurement studies retain compact protocols/results; temporary study
fixtures and one-use drivers were removed. Historical reproduction requires the
recorded revision.
