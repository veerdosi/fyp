"""Recover an interrupted episode from its exact logged native actions.

This is offline recovery, not a policy routine or a new experimental condition.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

run = Path(__file__).resolve().parent
root = run.parents[1]
sys.path.insert(0, str(root / 'src'))
from fyp.episode import Episode, serve, write_json
from fyp.runtime import CAMERAS, add_robot_sensors, make_env, proprio, sensor_images

assert not (run / 'outcome.json').exists(), 'Episode already terminal'
config = json.loads((run / 'config.json').read_text())
protocol = json.loads((root / 'studies/tool_hang_v1/protocol.json').read_text())
for path, expected in {**protocol['source_hashes'], **protocol['material_hashes']}.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path
assert {str(p.relative_to(root)) for d in ['src', 'scripts'] for p in (root/d).rglob('*.py')} == set(protocol['source_hashes'])
source = (run / 'steps.jsonl').read_bytes()
records = [json.loads(line) for line in source.decode().splitlines()]
commands = [json.loads(line) for line in (run / 'commands.jsonl').read_text().splitlines()]
assert len(records) == 280 and len(commands) == 3, 'Recovery applies only to this recorded interruption'
latest = json.loads((run / 'public/latest.json').read_text())
env, obs, initial = make_env(**{k: config[k] for k in ['task', 'suite', 'state_index', 'seed', 'size']})
assert np.array_equal(initial, np.load(run / 'initial_state.npy'))
errors = dict(robot_before=0., robot_after=0., private_objects=0., final_depth=0.)
score_mismatches = 0
states, actions = [], []
video = imageio.get_writer(str(run / 'episode_recovered.mp4'), fps=20)
for record in records:
    for key, expected in record['executor_measurement'].items():
        errors['robot_before'] = max(errors['robot_before'], float(np.max(np.abs(np.array(proprio(obs)[key])-expected))))
    action = np.array(record['action'])
    obs, _, _, _ = env.step(action)
    add_robot_sensors(env, obs)
    for key, expected in record['proprioception_after'].items():
        errors['robot_after'] = max(errors['robot_after'], float(np.max(np.abs(np.array(proprio(obs)[key])-expected))))
    for key, expected in record['diagnostic_object_observations'].items():
        errors['private_objects'] = max(errors['private_objects'], float(np.max(np.abs(obs[key]-expected))))
    score_mismatches += int(bool(env.check_success()) != record['scoring_success'] or env.diagnostic_goals() != record['diagnostic_goal_predicates'])
    states.append(env.get_sim_state().copy())
    actions.append(action.tolist())
    video.append_data(np.concatenate([obs[n+'_image'][::-1] for n in CAMERAS], axis=1))
rgb_match = True
from PIL import Image
for name, (rgb, depth) in sensor_images(env, obs).items():
    folder = Path(latest['folder'])
    rgb_match &= np.array_equal(rgb, np.array(Image.open(folder/(name+'.png'))))
    errors['final_depth'] = max(errors['final_depth'], float(np.max(np.abs(depth-np.load(folder/(name+'_depth_m.npy'))))))
passed = max(errors.values()) < 1e-7 and score_mismatches == 0 and rgb_match
verification = dict(pass_verification=passed, control_steps=len(records), max_measurement_errors=errors,
                    scoring_mismatches=score_mismatches, final_rgb_exact=bool(rgb_match),
                    prefix_sha256=hashlib.sha256(source).hexdigest(), code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    frozen_source_verified=True, restored_decisions=len(commands),
                    note='No commands, observations or budgets reset. Original process handle missing and process inventory confirmed absent. Same episode reconstructed before continuing pending policy decision.',
                    wall_time_note='Original monotonic clock unavailable. Post-recovery wall clock uses config mtime minus recorded setup duration as an approximate origin; includes interruption and reconstruction. Exclude from completion-speed claims.',
                    video='episode_recovered.mp4', reproduce='.venv/bin/python runs/th_v1_s02_deadline_guard/resume_episode.py')
write_json(run/'recovery_verification.json', verification)
print(json.dumps(verification), flush=True)
if not passed:
    video.close()
    env.close()
    raise SystemExit('Recovery verification failed; no continuation allowed')
np.savez_compressed(run/'recovery_checkpoint.npz', initial=initial, actions=np.array(actions), states=np.array(states))
ep = Episode.__new__(Episode)
ep.folder, ep.public, ep.config = run, run/'public', config
ep.env, ep.obs, ep.initial = env, obs, initial
ep.steps, ep.calls, ep.handoff = len(records), len(commands), latest['observation_id']+1
ep.closed = False
ep.max_steps, ep.max_calls = config['max_steps'], config['max_calls']
ep.t0 = time.monotonic() - (time.time() - (run/'config.json').stat().st_mtime + config['setup_wall_seconds'])
ep.log = (run/'steps.jsonl').open('a')
ep.events = (run/'commands.jsonl').open('a')
ep.states, ep.actions, ep.video, ep.latest = states, actions, video, latest
serve(ep, 8765)
