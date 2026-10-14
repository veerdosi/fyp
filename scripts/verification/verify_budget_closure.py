"""Run from the repository root, passing an unused output directory.

Example: .venv/bin/python scripts/verification/verify_budget_closure.py /tmp/fyp-budget-check
No model is invoked. This exercises the real environment and episode recorder.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from fyp.episode import Episode, write_json

run = Path(sys.argv[1])
episode = Episode(run, task='ToolHang', suite='robosuite', seed=499,
                  condition='fixed_sequence', max_calls=1)
reply = episode.command({'command': {'type': 'move', 'waypoints': [],
                        'reason': 'Operator verification of rejected-decision budget closure; no robot policy invocation.'}})
assert episode.closed and reply['episode_stopped'] == 'budget_exhausted'
assert episode.calls == 1 and episode.steps == 20
assert json.loads((run / 'outcome.json').read_text())['stop_reason'] == 'model_call_budget'
episode.events.close()
write_json(run / 'operator_verification.json', {
    'passed': True, 'policy_inference_requests': 0, 'submitted_operator_requests': 1,
    'check': 'The final invalid decision consumes the budget and closes the run without additional motion.',
    'reply': reply})
print(json.dumps({'passed': True, 'control_steps': 20, 'policy_inference_requests': 0}))
