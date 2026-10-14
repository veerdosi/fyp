"""Zero-inference end-to-end audit of the current timed baseline."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from fyp.episode import Episode, replay, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('pilot', choices=['pilot_tool_hang_001', 'pilot_tool_hang_002'])
parser.add_argument('--run', type=Path, help='Fresh output folder; defaults outside the repository.')
args = parser.parse_args()
source = ROOT / 'runs' / args.pilot
config = json.loads((source / 'config.json').read_text())
suffix = args.pilot.rsplit('_', 1)[1]
run = args.run or Path(tempfile.mkdtemp(prefix='fyp-pilot-replay-')) / 'episode'
ep = Episode(run, **{k: config[k] for k in ['task', 'suite', 'seed', 'state_index',
             'condition', 'size', 'max_steps', 'max_calls', 'settle_steps']})
ep.config.update(model=None, reasoning_effort=None, verification=dict(
    type='recorded_model_command_reexecution', source_pilot=args.pilot,
    source_command_sha256=hashlib.sha256((source / 'commands.jsonl').read_bytes()).hexdigest(),
    source_trajectory_sha256=hashlib.sha256((source / 'trajectory.npz').read_bytes()).hexdigest(),
    verification_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    actual_model_inference_requests=0,
    budget_note='Command counter is retained by generic Episode; no new model decision or inference occurred.'))
write_json(run / 'config.json', ep.config)
assert np.array_equal(np.load(source / 'initial_state.npy'), ep.initial)
commands = [json.loads(line)['command'] for line in (source / 'commands.jsonl').read_text().splitlines()]
for command in commands:
    assert not ep.closed, 'Verification stopped before the original command sequence ended'
    ep.command(dict(command=command, policy=None))
assert ep.closed, 'Original command sequence did not finish'
original, current = np.load(source / 'trajectory.npz'), np.load(run / 'trajectory.npz')
errors = {}
for key in ['actions', 'states']:
    assert original[key].shape == current[key].shape, f'{key} shape mismatch'
    errors[key] = float(np.max(np.abs(original[key] - current[key])))
outcome = json.loads((run / 'outcome.json').read_text())
expected = json.loads((source / 'outcome.json').read_text())
passed = max(errors.values()) <= 1e-7 and outcome['success'] == expected['success']
report = dict(source_pilot=args.pilot, verification_run=str(run),
              exact_commands_reexecuted=len(commands), actual_model_inference_requests=0,
              maximum_errors=errors, current_success=outcome['success'],
              original_success=expected['success'], pass_verification=passed,
              scope='Checks current physical execution with original commands; not a new policy episode, success-rate estimate or pilot prompt equivalence test.',
              reproduce=f'.venv/bin/python studies/tool_hang_v1/reexecute_pilot_commands.py {args.pilot}')
write_json(run / 'command_reexecution_verification.json', report)
replay(run)
print(json.dumps(report, indent=2))
if not passed:
    raise SystemExit(1)
