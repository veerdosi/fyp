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
from fyp.episode import serve, write_json
from fyp.pose_preview import PosePreviewEpisode
from fyp.kinematic_preview import Preview
from fyp.sensor_monitor import SensorMonitor
from scipy.spatial.transform import Rotation
from fyp.runtime import CAMERAS, add_robot_sensors, make_env, proprio, sensor_images

assert not (run / 'outcome.json').exists(), 'Episode already terminal'
config = json.loads((run / 'config.json').read_text())
import importlib.metadata
assert all(importlib.metadata.version(n)==v for n,v in config['versions'].items()), 'Runtime versions changed'
protocol = json.loads((root / 'studies/pose_feasibility_v1/protocol.json').read_text())
for path, expected in {**protocol['source_hashes'], **protocol['material_hashes']}.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path
assert {str(p.relative_to(root)) for d in ['src', 'scripts'] for p in (root/d).rglob('*.py')} == set(protocol['source_hashes'])
source = (run / 'steps.jsonl').read_bytes()
records = [json.loads(line) for line in source.decode().splitlines()]
commands = [json.loads(line) for line in (run / 'commands.jsonl').read_text().splitlines()]
assert len(records) >= config['settle_steps'] and commands, 'No complete recorded prefix'
assert records[-1]['step'] == len(records)
assert commands[-1]['call'] == len(commands)
latest = json.loads((run / 'public/latest.json').read_text())
env, obs, initial = make_env(**{k: config[k] for k in ['task', 'suite', 'state_index', 'seed', 'size']})
assert np.array_equal(initial, np.load(run / 'initial_state.npy'))
errors = dict(robot_before=0., robot_after=0., private_objects=0., final_depth=0.)
score_mismatches = 0
states, actions = [], []
feedback_rows = [json.loads(line) for line in (run/'sensor_feedback.jsonl').read_text().splitlines()]
feedback_by_step = {row['step']: row for row in feedback_rows}
command_by_id = {command['call']: command for command in commands}
calibration = config['sensor_feedback']['calibration']
monitor = SensorMonitor(calibration['weights'], calibration['empty_max'])
history, previous_waypoint, monitor_checks = [], None, 0
video_name = f'episode_recovered_{len(records)}.mp4'
video = imageio.get_writer(str(run / video_name), fps=20)
for record in records:
    for key, expected in record['executor_measurement'].items():
        errors['robot_before'] = max(errors['robot_before'], float(np.max(np.abs(np.array(proprio(obs)[key])-expected))))
    before = proprio(obs)
    feedback_row = feedback_by_step.get(record['step'])
    if feedback_row:
        waypoint = (feedback_row['command_id'], feedback_row['waypoint_index'])
        wp = command_by_id[waypoint[0]]['command']['waypoints'][waypoint[1]]
        if waypoint != previous_waypoint:
            qgoal = Rotation.from_quat(wp.get('quaternion_xyzw', obs['robot0_eef_quat']))
            monitor.begin(dict(wp, quaternion_xyzw=qgoal.as_quat().tolist()), history[-3:])
            previous_waypoint = waypoint
    action = np.array(record['action'])
    obs, _, _, _ = env.step(action)
    add_robot_sensors(env, obs)
    for key, expected in record['proprioception_after'].items():
        errors['robot_after'] = max(errors['robot_after'], float(np.max(np.abs(np.array(proprio(obs)[key])-expected))))
    for key, expected in record['diagnostic_object_observations'].items():
        errors['private_objects'] = max(errors['private_objects'], float(np.max(np.abs(obs[key]-expected))))
    score_mismatches += int(bool(env.check_success()) != record['scoring_success'] or env.diagnostic_goals() != record['diagnostic_goal_predicates'])
    after = proprio(obs)
    if feedback_row:
        measured = dict(step=record['step'], command_id=feedback_row['command_id'], waypoint_index=feedback_row['waypoint_index'], armed=wp.get('abort_if_empty_close', False), **monitor.update(before, after))
        assert measured == feedback_row, 'Feedback reconstruction differs'
        monitor_checks += 1
    history.append(after)
    history = history[-3:]
    states.append(env.get_sim_state().copy())
    actions.append(action.tolist())
    video.append_data(np.concatenate([obs[n+'_image'][::-1] for n in CAMERAS], axis=1))
rgb_match = True
from PIL import Image
for name, (rgb, depth) in sensor_images(env, obs).items():
    folder = Path(latest['folder'])
    rgb_match &= np.array_equal(rgb, np.array(Image.open(folder/(name+'.png'))))
    errors['final_depth'] = max(errors['final_depth'], float(np.max(np.abs(depth-np.load(folder/(name+'_depth_m.npy'))))))
passed = max(errors.values()) == 0. and score_mismatches == 0 and rgb_match
verification = dict(pass_verification=passed, control_steps=len(records), max_measurement_errors=errors,
                    scoring_mismatches=score_mismatches, final_rgb_exact=bool(rgb_match), monitor_rows_exact=monitor_checks,
                    prefix_sha256=hashlib.sha256(source).hexdigest(), code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    frozen_source_verified=True, restored_decisions=len(commands),
                    note='No commands, observations or budgets reset. Original process handle missing and process inventory confirmed absent. Same episode reconstructed before continuing pending policy decision.',
                    wall_time_note='Original monotonic clock unavailable. Post-recovery wall clock uses config mtime minus recorded setup duration as an approximate origin; includes interruption and reconstruction. Exclude from completion-speed claims.',
                    original_full_state_prefix_available=False, original_recorded_robot_object_scoring_prefix_exact=True, reconstructed_state_prefix_saved=True,
                    video=video_name, reproduce='.venv/bin/python runs/pf_v1_s02_preview/resume_episode.py')
write_json(run/f'recovery_verification_{len(records)}.json', verification)
write_json(run/'recovery_verification.json', verification)
print(json.dumps(verification), flush=True)
if not passed:
    video.close()
    env.close()
    raise SystemExit('Recovery verification failed; no continuation allowed')
np.savez_compressed(run/'recovery_checkpoint.npz', initial=initial, actions=np.array(actions), states=np.array(states))
ep = PosePreviewEpisode.__new__(PosePreviewEpisode)
ep.preview_enabled=config["pose_preview"]["enabled"]
ep.solver_parameters=config["pose_preview"]["parameters"]
robot_folder=run/"public/robot_kinematics"
ep.preview=Preview((robot_folder/"robot.xml").read_text(),ep.solver_parameters)
ep.interrupt_empty = config['sensor_feedback']['interrupt_empty']
ep.feedback, ep.feedback_rows, ep.robot_history = monitor, feedback_rows, history
ep.folder, ep.public, ep.config = run, run/'public', config
ep.env, ep.obs, ep.initial = env, obs, initial
ep.steps, ep.calls, ep.handoff = len(records), len(commands), latest['observation_id']+1
ep.closed = False
ep.max_steps, ep.max_calls = config['max_steps'], config['max_calls']
ep.t0 = time.monotonic() - (time.time() - (run/'config.json').stat().st_mtime + config['setup_wall_seconds'])
ep.log = (run/'steps.jsonl').open('a')
ep.events = (run/'commands.jsonl').open('a')
ep.states, ep.actions, ep.video, ep.latest = states, actions, video, latest
serve(ep, 8768)
