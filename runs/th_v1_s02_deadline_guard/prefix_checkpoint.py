"""Reconstruct and verify the logged interrupted prefix without moving the live robot."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

run = Path(__file__).resolve().parent
sys.path.insert(0, str(run.parents[1] / 'src'))
from fyp.runtime import add_robot_sensors, make_env, proprio

config = json.loads((run / 'config.json').read_text())
source = (run / 'steps.jsonl').read_bytes()
records = [json.loads(line) for line in source.decode().splitlines()]
initial = np.load(run / 'initial_state.npy')
env, obs, generated_initial = make_env(**{k: config[k] for k in ['task', 'suite', 'state_index', 'seed', 'size']})
# The live constructor keeps reset's observable caches. Re-setting an identical
# simulator state re-samples cached observations and changes their phase/signs.
# Reproduce the actual constructor rather than altering those caches.
assert np.array_equal(generated_initial, initial), 'Initial state differs'
states, actions = [], []
errors = dict(robot_before=0.0, robot_after=0.0, private_object_observations=0.0)
per_key = {}
first_difference = {}
score_mismatches = 0
for record in records:
    before = proprio(obs)
    for key, expected in record['executor_measurement'].items():
        errors['robot_before'] = max(errors['robot_before'], float(np.max(np.abs(np.array(before[key]) - expected))))
    action = np.array(record['action'])
    obs, _, _, _ = env.step(action)
    add_robot_sensors(env, obs)
    after = proprio(obs)
    for key, expected in record['proprioception_after'].items():
        error = float(np.max(np.abs(np.array(after[key]) - expected)))
        errors['robot_after'] = max(errors['robot_after'], error)
        per_key[key] = max(per_key.get(key, 0.0), error)
        if error > 1e-7:
            first_difference.setdefault(key, record['step'])
    for key, expected in record['diagnostic_object_observations'].items():
        error = float(np.max(np.abs(obs[key] - expected)))
        errors['private_object_observations'] = max(errors['private_object_observations'], error)
        per_key[key] = max(per_key.get(key, 0.0), error)
        if error > 1e-7:
            first_difference.setdefault(key, record['step'])
    if bool(env.check_success()) != record['scoring_success'] or env.diagnostic_goals() != record['diagnostic_goal_predicates']:
        score_mismatches += 1
    states.append(env.get_sim_state().copy())
    actions.append(action)
passed = max(errors.values()) < 1e-7 and score_mismatches == 0
result = dict(scope='Interrupted prefix verification, not a completed trial or full saved-state replay.',
              control_steps=len(records), max_measurement_errors=errors,
              errors_by_key=per_key, first_difference_step=first_difference,
              score_mismatches=score_mismatches, pass_verification=passed,
              final_native_success=bool(env.check_success()), final_private_goals=env.diagnostic_goals(),
              logged_prefix_sha256=hashlib.sha256(source).hexdigest(),
              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              reproduce='.venv/bin/python runs/th_v1_s02_deadline_guard/prefix_checkpoint.py',
              checkpoint_note='States reconstructed from logged native actions and verified against every recorded robot/object measurement and score. Compare against the live episode saved states when it finishes.')
if passed:
    np.savez_compressed(run / 'interruption_checkpoint.npz', initial=initial,
                        actions=np.array(actions), states=np.array(states))
(run / 'prefix_checkpoint_verification.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
env.close()
if not passed:
    raise SystemExit(1)
