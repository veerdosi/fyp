"""Reconstruct actions, states, public sensors and guarded measurements once."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env, proprio, add_robot_sensors, sensor_images
from fyp.sensor_monitor import SensorMonitor, compensate, opening
from robosuite.utils.camera_utils import get_camera_intrinsic_matrix, get_camera_extrinsic_matrix


def load(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--run', required=True, type=Path)
args = p.parse_args()
run = args.run.resolve()
config = load(run / 'config.json')
saved = np.load(run / 'trajectory.npz')
steps = lines(run / 'steps.jsonl')
commands = {c['call']: c for c in lines(run / 'commands.jsonl')}
feedback = {r['step']: r for r in lines(run / 'sensor_feedback.jsonl')}
snapshots = {load(f / 'observation.json')['step']: f for f in (run / 'public').glob('obs_*')}
calibration = config['sensor_feedback']['calibration']
monitor = SensorMonitor(calibration['weights'], calibration['empty_max'])
env, obs, initial = make_env(**{k: config[k] for k in ['task', 'suite', 'seed', 'state_index', 'size']})
assert np.array_equal(initial, saved['initial'])
history = []
previous_waypoint = None
state_error = sensor_error = calibration_error = 0.
camera_checks = monitor_checks = native_checks = action_checks = 0

for index, action in enumerate(saved['actions']):
    before = proprio(obs)
    row = feedback.get(index + 1)
    if row:
        waypoint = (row['command_id'], row['waypoint_index'])
        command = commands[row['command_id']]
        wp = command['command']['waypoints'][row['waypoint_index']]
        if waypoint != previous_waypoint:
            qgoal = Rotation.from_quat(wp.get('quaternion_xyzw', obs['robot0_eef_quat']))
            monitor.begin(dict(wp, quaternion_xyzw=qgoal.as_quat().tolist()), history[-3:])
            previous_waypoint = waypoint
        dp = np.asarray(wp['position']) - obs['robot0_eef_pos']
        norm = np.linalg.norm(dp)
        if norm > .015:
            dp *= .015 / norm
        dr = (qgoal * Rotation.from_quat(obs['robot0_eef_quat']).inv()).as_rotvec()
        angle = np.linalg.norm(dr)
        if angle > .15:
            dr *= .15 / angle
        expected_action = np.r_[np.clip(np.r_[dp, dr] / env.robots[0].controller.output_max, -1, 1), wp['gripper']]
        assert np.array_equal(expected_action, action)
        action_checks += 1
    obs, _, _, _ = env.step(action)
    add_robot_sensors(env, obs)
    after = proprio(obs)
    state_error = max(state_error, float(np.max(np.abs(env.get_sim_state() - saved['states'][index]))))
    for key, expected in steps[index]['proprioception_after'].items():
        sensor_error = max(sensor_error, float(np.max(np.abs(np.asarray(after[key]) - expected))))
    assert env.diagnostic_goals() == steps[index]['diagnostic_goal_predicates']
    native_checks += 1
    history.append(after)
    history = history[-3:]
    if row:
        actual = dict(step=index + 1, command_id=row['command_id'], waypoint_index=row['waypoint_index'],
                      armed=wp.get('abort_if_empty_close', False), **monitor.update(before, after))
        assert actual == row
        monitor_checks += 1
        if config['sensor_feedback']['interrupt_empty'] and row['armed'] and row['flags']['empty_sized_closure']:
            report = command['result']['execution_report']
            assert report['stop_reason'] == 'armed_empty_sized_closure'
            assert report['waypoints'][-1]['last_step'] == index + 1
    folder = snapshots.get(index + 1)
    if folder:
        recorded_calibration = load(folder / 'calibration.json')
        for camera, (rgb, depth) in sensor_images(env, obs).items():
            assert np.array_equal(rgb, np.asarray(Image.open(folder / (camera + '.png'))))
            assert np.array_equal(depth, np.load(folder / (camera + '_depth_m.npy')))
            for key, actual in [('intrinsic', get_camera_intrinsic_matrix(env.sim, camera, *rgb.shape[:2])),
                                ('camera_to_world', get_camera_extrinsic_matrix(env.sim, camera))]:
                calibration_error = max(calibration_error, float(np.max(np.abs(
                    actual - np.asarray(recorded_calibration[camera][key])))))
            camera_checks += 1
        public = load(folder / 'sensor_feedback.json')
        assert public['opening_m'] == opening(after)
        assert public['current_compensated_wrench'] == compensate(after, monitor.weights).tolist()

outcome = load(run / 'outcome.json')
assert bool(env.check_success()) == outcome['success']
assert env.diagnostic_goals() == outcome['diagnostic_goal_predicates']
env.close()
assert state_error == sensor_error == calibration_error == 0.
result = dict(all_pass=True, steps=len(steps), max_state_absolute_error=state_error,
              max_public_sensor_absolute_error=sensor_error, max_calibration_absolute_error=calibration_error,
              camera_snapshot_checks=camera_checks, monitor_rows_exact=monitor_checks,
              action_conversion_checks=action_checks, native_checks=native_checks,
              native_outcome_matches=True, actual_astra_requests=0,
              initialization='Original seeded initialization and observable sampling; no forced state/update.',
              command=f'.venv/bin/python studies/tool_hang_v2/replay.py --run {run}',
              replay_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(run / 'replay_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
