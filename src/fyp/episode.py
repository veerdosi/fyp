"""Direct pose/waypoint execution, recording, and replay for LIBERO.

The public boundary contains RGB-D, camera calibration and robot sensors only.
Reward and object state are recorded separately and never determine commands.
"""
import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

from .runtime import ROOT, TASK, CAMERAS, PROPRIO, make_env, proprio, sensor_images, add_robot_sensors


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False))


def revision(folder=ROOT):
    return subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()


class Episode:
    def __init__(self, folder, task=TASK, suite='libero_10', state_index=0, seed=0,
                 condition='direct_waypoints', size=256, max_steps=2400, max_calls=30,
                 settle_steps=20):
        self.folder = Path(folder).resolve()
        self.folder.mkdir(parents=True, exist_ok=False)
        self.public = self.folder / 'public'
        self.public.mkdir()
        self.t0 = time.monotonic()
        self.steps = self.calls = self.handoff = 0
        self.closed = False
        self.max_steps, self.max_calls = max_steps, max_calls
        self.env, self.obs, initial = make_env(task, suite, state_index, seed, size)
        self.initial = initial
        np.save(self.folder / 'initial_state.npy', initial)
        config = dict(task=task, suite=suite, state_index=state_index, seed=seed,
                      condition=condition, size=size, max_steps=max_steps, max_calls=max_calls,
                      settle_steps=settle_steps,
                      code_revision=revision(),
                      code_dirty=bool(subprocess.check_output(
                          ['git','status','--porcelain','--','src','scripts','requirements.in','requirements.lock'], cwd=ROOT)),
                      source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted((ROOT/'src').rglob('*.py'))},
                      libero_revision=revision(ROOT / 'vendor/LIBERO'),
                      model=None if condition=='fixed_sequence' else 'gpt-6-astra',
                      reasoning_effort=None if condition=='fixed_sequence' else 'medium',
                      simulation_paused_during_inference=True, control_freq=20,
                      versions={n: importlib.metadata.version(n) for n in
                                ['numpy', 'mujoco', 'robosuite', 'torch']})
        self.config = config
        write_json(self.folder / 'config.json', config)
        self.log = (self.folder / 'steps.jsonl').open('w')
        self.events = (self.folder / 'commands.jsonl').open('w')
        self.states = []
        self.actions = []
        import imageio.v2 as imageio
        self.video = imageio.get_writer(str(self.folder / 'episode.mp4'), fps=20)
        for _ in range(settle_steps):
            self.step(np.array([0,0,0,0,0,0,-1.0]), 'initial_settle')
        self.snapshot()

    def snapshot(self):
        from robosuite.utils.camera_utils import get_camera_intrinsic_matrix, get_camera_extrinsic_matrix
        folder = self.public / f'obs_{self.handoff:04d}'
        folder.mkdir()
        sensors = sensor_images(self.env, self.obs)
        calibration = {}
        for name, (rgb, depth) in sensors.items():
            Image.fromarray(rgb).save(folder / (name + '.png'))
            np.save(folder / (name + '_depth_m.npy'), depth)
            calibration[name] = dict(
                intrinsic=get_camera_intrinsic_matrix(self.env.sim, name, *rgb.shape[:2]).tolist(),
                camera_to_world=get_camera_extrinsic_matrix(self.env.sim, name).tolist(),
                image_convention='top-left origin; u right, v down; optical depth in metres')
        write_json(folder / 'calibration.json', calibration)
        result = dict(observation_id=self.handoff, step=self.steps,
                      simulated_seconds=self.steps / 20, model_calls=self.calls,
                      remaining_steps=self.max_steps-self.steps,
                      remaining_model_calls=self.max_calls-self.calls,
                      proprioception=proprio(self.obs), folder=str(folder),
                      cameras={n: str(folder / (n + '.png')) for n in CAMERAS})
        write_json(folder / 'observation.json', result)
        write_json(self.public / 'latest.json', result)
        self.latest = result
        self.handoff += 1
        return result

    def step(self, action, command_id=None):
        if self.steps >= self.max_steps:
            raise ValueError('control-step budget exhausted')
        before = proprio(self.obs)
        self.obs, reward, done, info = self.env.step(action)
        add_robot_sensors(self.env, self.obs)
        self.steps += 1
        self.actions.append(action.tolist())
        self.states.append(self.env.get_sim_state().copy())
        record = dict(step=self.steps, command_id=command_id, action=action.tolist(),
                      executor_measurement=before, proprioception_after=proprio(self.obs),
                      scoring_success=bool(self.env.check_success()), reward=float(reward),
                      done=bool(done), wall_seconds=time.monotonic()-self.t0)
        # Object observations belong only to diagnosis; never feed them back into action execution.
        record['diagnostic_object_observations'] = {
            k: v.tolist() for k, v in self.obs.items()
            if not k.startswith('robot') and not k.endswith(('_image', '_depth'))}
        record['diagnostic_goal_predicates'] = self.goal_predicates()
        self.log.write(json.dumps(record, allow_nan=False) + '\n')
        self.log.flush()
        rgb = [self.obs[n + '_image'][::-1] for n in CAMERAS]
        self.video.append_data(np.concatenate(rgb, axis=1))

    def goal_predicates(self):
        # Scoring only. No executor or public input reads these values.
        return [{'predicate':state, 'satisfied':bool(self.env.env._eval_predicate(state))}
                for state in self.env.env.parsed_problem['goal_state']]

    def validate_move(self, command):
        points = command.get('waypoints')
        limit = 1 if self.config['condition'] == 'direct_pose' else 4
        if not isinstance(points, list) or not 1 <= len(points) <= limit:
            raise ValueError(f'waypoints must contain 1..{limit} targets')
        total = 0
        for wp in points:
            p = np.asarray(wp.get('position'), dtype=float)
            q = np.asarray(wp.get('quaternion_xyzw', self.obs['robot0_eef_quat']), dtype=float)
            if p.shape != (3,) or not np.all(np.isfinite(p)):
                raise ValueError('position must be three finite metres')
            if np.any(p < [-0.55, -0.55, 0.76]) or np.any(p > [0.55, 0.65, 1.6]):
                raise ValueError('target outside workspace bounds')
            if q.shape != (4,) or not np.all(np.isfinite(q)) or abs(np.linalg.norm(q)-1)>0.01:
                raise ValueError('quaternion_xyzw must be unit length')
            if wp.get('gripper') not in [-1, 1]:
                raise ValueError('gripper must be -1=open or +1=close')
            if type(wp.get('steps')) is not int or not 1 <= wp['steps'] <= 100:
                raise ValueError('steps must be an integer 1..100')
            total += wp['steps']
        if total > 200 or total > self.max_steps-self.steps:
            raise ValueError('command exceeds 200 steps or episode step budget')
        return points

    def move(self, points):
        controller = self.env.robots[0].controller
        outmax = np.asarray(controller.output_max)
        # A fixed absolute pose is realized using the existing OSC_POSE controller.
        # The conversion uses only measured end-effector pose, not an object estimate.
        for wp in points:
            goal = np.asarray(wp['position'])
            qgoal = Rotation.from_quat(wp.get('quaternion_xyzw', self.obs['robot0_eef_quat']))
            for _ in range(wp['steps']):
                p = self.obs['robot0_eef_pos']
                r = Rotation.from_quat(self.obs['robot0_eef_quat'])
                dp = goal - p
                norm = np.linalg.norm(dp)
                if norm > 0.015:
                    dp *= 0.015/norm
                dr = (qgoal * r.inv()).as_rotvec()
                angle = np.linalg.norm(dr)
                if angle > 0.15:
                    dr *= 0.15/angle
                action = np.r_[np.clip(np.r_[dp, dr]/outmax, -1, 1), wp['gripper']]
                self.step(action, self.calls)

    def sense(self, points):
        if not isinstance(points, list) or not 1 <= len(points) <= 12:
            raise ValueError('pixels must contain 1..12 camera/u/v selections')
        folder = Path(self.latest['folder'])
        calibration = json.loads((folder / 'calibration.json').read_text())
        results = []
        for point in points:
            name = point['camera']
            if name not in CAMERAS:
                raise ValueError('unknown camera')
            u, v = point['u'], point['v']
            depth = np.load(folder / (name + '_depth_m.npy'))
            if type(u) is not int or type(v) is not int or not (0<=v<depth.shape[0] and 0<=u<depth.shape[1]):
                raise ValueError('pixel coordinates must be in image bounds')
            z = float(depth[v, u])
            cam = calibration[name]
            local = np.linalg.inv(np.asarray(cam['intrinsic'])) @ np.array([u,v,1.0])*z
            world = np.asarray(cam['camera_to_world']) @ np.r_[local,1]
            results.append(dict(camera=name, u=u, v=v, depth_m=z, world_xyz=world[:3].tolist()))
        return dict(observation_id=self.latest['observation_id'], points=results,
                    step=self.steps, model_calls=self.calls,
                    remaining_model_calls=self.max_calls-self.calls)

    def command(self, body):
        if self.closed:
            raise ValueError('episode already closed')
        if self.calls >= self.max_calls:
            raise ValueError('model-call budget exhausted')
        policy = body.get('policy')
        if policy:
            if policy.get('model') != 'gpt-6-astra' or policy.get('reasoning_effort') != 'medium':
                raise ValueError('robot policy must be gpt-6-astra at medium effort')
        self.calls += 1
        write_json(self.folder / f'policy_turn_{self.calls:03d}.json', body)
        cmd = body['command']
        event = dict(call=self.calls, input_observation_id=self.latest['observation_id'],
                     command=cmd, wall_seconds=time.monotonic()-self.t0)
        try:
            if cmd['type'] == 'move':
                self.move(self.validate_move(cmd))
                result = self.snapshot()
            elif cmd['type'] == 'sense':
                result = self.sense(cmd['pixels'])
            elif cmd['type'] == 'finish':
                result = {'finished': True, 'step': self.steps, 'policy_claim': cmd.get('reason')}
                self.finish('policy_finish')
            else:
                raise ValueError('type must be move, sense or finish')
            if not self.closed and (self.steps>=self.max_steps or self.calls>=self.max_calls):
                self.finish('control_budget' if self.steps>=self.max_steps else 'model_call_budget')
                result['episode_stopped'] = 'budget_exhausted'
            event['result'] = result
        except (ValueError, KeyError, TypeError) as exc:
            result = dict(validation_error=str(exc), observation=self.latest)
            event['result'] = result
        self.events.write(json.dumps(event, allow_nan=False)+'\n')
        self.events.flush()
        return result

    def finish(self, stop_reason):
        if self.closed:
            return
        self.closed = True
        self.video.close()
        self.log.close()
        np.savez_compressed(self.folder / 'trajectory.npz',
                            initial=self.initial, actions=np.asarray(self.actions).reshape(-1,7),
                            states=np.asarray(self.states))
        write_json(self.folder / 'outcome.json', dict(
            success=bool(self.env.check_success()), stop_reason=stop_reason,
            diagnostic_goal_predicates=self.goal_predicates(),
            control_steps=self.steps, simulated_seconds=self.steps/20,
            wall_seconds=time.monotonic()-self.t0, model_calls=self.calls,
            cost_usd=None if self.calls else 0,
            cost_status='unavailable for collaboration policy calls' if self.calls else 'no model calls',
            replay_command=f'.venv/bin/python scripts/episode.py replay --run {self.folder}'))
        self.env.close()


def serve(episode, port):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                result = episode.command(body)
            except Exception as exc:
                result = {'error': type(exc).__name__+': '+str(exc)}
            payload = json.dumps(result).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = HTTPServer(('127.0.0.1', port), Handler)
    server.timeout = 0.5
    print(json.dumps({'ready': True, 'port': port, 'observation': episode.latest}), flush=True)
    try:
        while not episode.closed:
            server.handle_request()
    finally:
        episode.finish('server_shutdown')
        episode.events.close()
        server.server_close()


def replay(folder):
    folder = Path(folder)
    config = json.loads((folder / 'config.json').read_text())
    saved = np.load(folder / 'trajectory.npz')
    env, obs, initial = make_env(**{k: config[k] for k in ['task','suite','state_index','seed','size']})
    obs = env.set_init_state(saved['initial'])
    errors = []
    for i, action in enumerate(saved['actions']):
        obs, reward, done, info = env.step(action)
        errors.append(float(np.max(np.abs(env.get_sim_state()-saved['states'][i]))))
    result = dict(control_steps=len(errors), max_state_absolute_error=max(errors,default=0),
                  success=bool(env.check_success()),
                  expected_success=json.loads((folder / 'outcome.json').read_text())['success'])
    result['pass'] = result['max_state_absolute_error'] < 1e-7 and result['success']==result['expected_success']
    write_json(folder / 'replay_verification.json', result)
    env.close()
    print(json.dumps(result))
    if not result['pass']:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['smoke','serve','replay'])
    parser.add_argument('--run', required=True)
    parser.add_argument('--state-index', type=int, default=0)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--settle-steps', type=int, default=20)
    parser.add_argument('--task', default=TASK)
    parser.add_argument('--suite', default='libero_10')
    parser.add_argument('--condition', choices=['direct_pose','direct_waypoints'], default='direct_waypoints')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.mode == 'replay':
        replay(args.run)
        return
    ep = Episode(args.run, task=args.task, suite=args.suite, state_index=args.state_index,
                 seed=args.seed, condition='fixed_sequence' if args.mode=='smoke' else args.condition,
                 settle_steps=args.settle_steps)
    if args.mode == 'serve':
        serve(ep, args.port)
    else:
        for i in range(40):
            ep.step(np.array([0.1 if i<20 else -0.1,0,0,0,0,0,-1.0]))
        ep.snapshot()
        ep.finish('fixed_sequence_complete')
        ep.events.close()
        print((ep.folder / 'outcome.json').read_text())
