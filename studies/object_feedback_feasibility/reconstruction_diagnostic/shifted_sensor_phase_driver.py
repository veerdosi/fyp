"""Replay sensor streams; keep private geometric reference outside the tracker."""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env, sensor_images
from robosuite.utils.camera_utils import get_camera_extrinsic_matrix, get_camera_intrinsic_matrix
from tracker import PARAMETERS, PointTracker, world_point


def ray_body(sim, origin, point):
    vector = np.asarray(point) - origin
    length = np.linalg.norm(vector)
    geom = np.array([-1], dtype=np.int32)
    group = sim._render_context_offscreen.vopt.geomgroup.copy()
    distance = mujoco.mj_ray(sim.model._model, sim.data._data, origin,
                             vector/length, group, 1, -1, geom)
    if distance < 0:
        return None, None
    return int(sim.model.geom_bodyid[geom[0]]), float(distance - length)


def reference(sim, pixel, depth, calibration):
    point = world_point(pixel, depth, calibration)
    if point is None:
        return None
    origin = np.asarray(calibration['camera_to_world'])[:3,3]
    body, residual = ray_body(sim, origin, point)
    if body is None or abs(residual) > .003:
        return None
    matrix = sim.data.xmat[body].reshape(3,3)
    return dict(body=body, local=matrix.T @ (point - sim.data.xpos[body]),
                body_name=sim.model.body_id2name(body), initial_ray_depth_residual_m=residual)


def truth(sim, ref, depth, calibration):
    if ref is None:
        return None, None
    point = sim.data.xmat[ref['body']].reshape(3,3) @ ref['local'] + sim.data.xpos[ref['body']]
    camera = np.asarray(calibration['camera_to_world'])
    optical = (np.linalg.inv(camera) @ np.r_[point,1])[:3]
    if optical[2] <= 0:
        return point, False
    image = np.asarray(calibration['intrinsic']) @ optical
    u, v = image[:2] / image[2]
    h, w = depth.shape
    x, y = int(round(u)), int(round(v))
    if not (0 <= x < w and 0 <= y < h):
        return point, False
    body, _ = ray_body(sim, camera[:3,3], point)
    visible = body == ref['body'] and abs(float(depth[y,x])-optical[2]) <= .003
    return point, bool(visible)


def summarize(rows):
    visible = [r for r in rows if r['reference_visible'] is True]
    occluded = [r for r in rows if r['reference_visible'] is False]
    accepted = [r for r in visible if r['accepted']]
    errors = [r['world_error_m'] for r in accepted]
    coverage = len(accepted)/len(visible) if visible else None
    false_valid = sum(r['accepted'] for r in occluded)/len(occluded) if occluded else None
    p95 = float(np.percentile(errors,95)) if errors else None
    return dict(samples=len(rows), reference_visible=len(visible), reference_occluded=len(occluded),
                reference_unknown=len(rows)-len(visible)-len(occluded), accepted_visible=len(accepted),
                visible_coverage=coverage, accepted_error_p95_m=p95,
                accepted_error_median_m=float(np.median(errors)) if errors else None,
                occluded_false_valid_rate=false_valid,
                gate_pass=coverage is not None and coverage >= .8 and p95 is not None and p95 <= .003
                          and false_valid is not None and false_valid <= .05)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--validation-only', action='store_true', help='Validate exact reconstruction of every query snapshot, without scoring the tracker.')
args = parser.parse_args()
parameters = json.loads((HERE/'parameters.json').read_text())
assert parameters['parameters'] == PARAMETERS
assert parameters['audit_driver_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
assert parameters['tracker_sha256'] == hashlib.sha256((HERE/'tracker.py').read_bytes()).hexdigest()
protocol = json.loads((ROOT/'studies/tool_hang_v1/protocol.json').read_text())
cohort, streams, skipped = [], [], []
for trial in protocol['episodes']:
    run = ROOT/'runs'/trial['episode_id']
    events = [json.loads(s) for s in (run/'commands.jsonl').read_text().splitlines()]
    steps = [json.loads(s) for s in (run/'steps.jsonl').read_text().splitlines()]
    group = {}
    for index, event in enumerate(events):
        if event['command']['type'] != 'sense':
            continue
        replies = event['result']['points']
        following = next((e for e in events[index+1:] if e['command']['type']=='move'), None)
        motion = [s for s in steps if following and s['command_id']==following['call']]
        if not motion:
            skipped += [dict(episode=run.name, query_decision=event['call'], pixel_index=i,
                             reason='no_following_executed_motion') for i in range(len(replies))]
            continue
        key = (event['result']['step'], motion[-1]['step'], event['input_observation_id'])
        item = group.setdefault(key, dict(episode=run.name, paired_state=trial['paired_state'],
                            condition=trial['condition'], start_step=key[0], end_step=key[1],
                            observation_id=key[2], motion_decision=following['call'], points=[]))
        for i, reply in enumerate(replies):
            item['points'].append(dict(query_decision=event['call'], pixel_index=i, **reply))
        initial_q = json.loads((run/f'public/obs_{key[2]:04d}/observation.json').read_text())['proprioception']['robot0_eef_quat']
        angles = [(Rotation.from_quat(s['proprioception_after']['robot0_eef_quat']) * Rotation.from_quat(initial_q).inv()).magnitude() for s in motion]
        item['motion_type'] = 'rotation' if max(angles) > .03 else 'translation'
    streams.extend(group.values())
    cohort.append(dict(episode=run.name, queries=sum(len(e['command'].get('pixels',[])) for e in events),
                       command_sha256=hashlib.sha256((run/'commands.jsonl').read_bytes()).hexdigest(),
                       trajectory_sha256=hashlib.sha256((run/'trajectory.npz').read_bytes()).hexdigest()))
manifest = dict(episodes=cohort, streams=streams, skipped_queries=skipped,
                query_count=sum(x['queries'] for x in cohort),
                retained_query_count=sum(len(x['points']) for x in streams),
                no_policy_inferences=True, mode='validation' if args.validation_only else 'complete_frozen_cohort')
(HERE/'cohort.json').write_text(json.dumps(manifest,indent=2))
rows, initial_points, reconstruction, replay_checks = [], [], [], []
limits = parameters['reconstruction_limits']
for trial in protocol['episodes']:
    run = ROOT/'runs'/trial['episode_id']
    config = json.loads((run/'config.json').read_text())
    saved = np.load(run/'trajectory.npz')
    env, _, _ = make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
    obs = env.set_init_state(saved['initial'])
    segments = [s for s in streams if s['episode']==run.name]
    active = []
    max_state_error = 0.
    for index, action in enumerate(saved['actions']):
        obs, _, _, _ = env.step(action)
        step = index+1
        error = float(np.max(np.abs(env.get_sim_state()-saved['states'][index])))
        max_state_error = max(max_state_error,error)
        assert error <= limits['state_absolute_error_max'], 'Action replay diverged'
        starting = [s for s in segments if s['start_step']==step]
        if not active and not starting:
            continue
        sensors = sensor_images(env,obs)
        calibration = {camera:dict(intrinsic=get_camera_intrinsic_matrix(env.sim,camera,*rgb.shape[:2]).tolist(),
                        camera_to_world=get_camera_extrinsic_matrix(env.sim,camera).tolist())
                       for camera,(rgb,depth) in sensors.items()}
        for segment, trackers, references, points in active:
            for camera, tracker in trackers.items():
                rgb, depth = sensors[camera]
                # Reference/body/visibility fields never enter the estimator.
                output = tracker.update(rgb,depth,calibration[camera])
                for p, ref, result in zip(points[camera],references[camera],output):
                    expected, visible = truth(env.sim,ref,depth,calibration[camera])
                    error = float(np.linalg.norm(np.array(result['world_xyz'])-expected)) if expected is not None and result['accepted'] else None
                    rows.append(dict(episode=run.name, paired_state=segment['paired_state'],
                        condition=segment['condition'], camera=camera,motion_type=segment['motion_type'],
                        query_decision=p['query_decision'],pixel_index=p['pixel_index'],step=step,
                        reference_visible=visible,world_error_m=error,**result))
        active = [a for a in active if a[0]['end_step']>step]
        for segment in starting:
            folder = run/f"public/obs_{segment['observation_id']:04d}"
            original_calibration = json.loads((folder/'calibration.json').read_text())
            trackers, references, points = {}, {}, {}
            for camera in sorted(set(p['camera'] for p in segment['points'])):
                rgb = np.asarray(Image.open(folder/(camera+'.png')))
                depth = np.load(folder/(camera+'_depth_m.npy'))
                replay_rgb, replay_depth = sensors[camera]
                pts = [p for p in segment['points'] if p['camera']==camera]
                pixels = [[p['u'],p['v']] for p in pts]
                depth_error = np.abs(depth-replay_depth)
                matches = dict(rgb_exact=np.array_equal(rgb,replay_rgb),
                    changed_rgb_fraction=float(np.mean(np.any(rgb!=replay_rgb,axis=2))),
                    rgb_max_absolute_error=int(np.max(np.abs(rgb.astype(int)-replay_rgb.astype(int)))),
                    depth_max_error_m=float(np.max(depth_error)),
                    depth_error_p99_m=float(np.percentile(depth_error,99)),
                    depth_outlier_fraction=float(np.mean(depth_error>limits['depth_error_m'])),
                    query_depth_max_error_m=float(max(depth_error[v,u] for u,v in pixels)),
                    calibration_max_error=float(max(np.max(np.abs(np.asarray(original_calibration[camera][key])-calibration[camera][key]))
                                                    for key in ['intrinsic','camera_to_world'])))
                matches['pass'] = (matches['changed_rgb_fraction'] <= limits['changed_rgb_fraction_max']
                    and matches['depth_outlier_fraction'] <= limits['depth_outlier_fraction_max']
                    and matches['query_depth_max_error_m'] <= limits['depth_error_m']
                    and matches['calibration_max_error'] <= limits['calibration_absolute_error_max'])
                reconstruction.append(dict(episode=run.name, observation_id=segment['observation_id'],camera=camera,**matches))
                # Save failures as evidence rather than losing them to an assertion.
                (HERE/'sensor_reconstruction.json').write_text(json.dumps(dict(checks=reconstruction,
                    all_pass=all(x['pass'] for x in reconstruction), limits=limits,replay_checks=replay_checks,
                    bit_exact_images=all(x['rgb_exact'] and x['depth_max_error_m']==0 for x in reconstruction)),indent=2))
                if not args.validation_only:
                    assert matches['pass'], f'Sensor reconstruction failed: {run.name}/{segment["observation_id"]}/{camera}: {matches}'
                if args.validation_only:
                    continue
                trackers[camera] = PointTracker(rgb,depth,original_calibration[camera],pixels)
                references[camera] = [reference(env.sim,p,depth,original_calibration[camera]) for p in pixels]
                points[camera] = pts
                for p, ref in zip(pts,references[camera]):
                    initial_points.append(dict(episode=run.name,**p,reference_available=ref is not None,
                        reference_body=ref['body_name'] if ref else None,
                        semantic_correctness='Not inferred from surface/body correspondence'))
            if not args.validation_only:
                active.append((segment,trackers,references,points))
            print(run.name,'snapshot',segment['observation_id'],'reconstruction checked',flush=True)
    replay_checks.append(dict(episode=run.name,steps=len(saved['actions']),max_state_absolute_error=max_state_error))
    env.close()
(HERE/'sensor_reconstruction.json').write_text(json.dumps(dict(checks=reconstruction,
    all_pass=all(x['pass'] for x in reconstruction),limits=limits,replay_checks=replay_checks,
    bit_exact_images=all(x['rgb_exact'] and x['depth_max_error_m']==0 for x in reconstruction),
    audit_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
if not args.validation_only:
    with gzip.open(HERE/'samples.jsonl.gz','wt') as f:
        for row in rows:
            f.write(json.dumps(row)+'\n')
    groups = {}
    for key in ['camera','motion_type','paired_state','condition']:
        groups[key] = {str(value):summarize([r for r in rows if r[key]==value]) for value in sorted(set(r[key] for r in rows))}
    summary = dict(scope='Observed-trace development feasibility audit; no task-success, guard-effect or held-out generalization claim.',
                   overall=summarize(rows),groups=groups,parameters=parameters,
                   initial_queries=initial_points,missing_following_motion=skipped,
                   actual_model_inference_requests=0,
                   audit_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'results.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary['overall'],indent=2))
else:
    print('Validated sensor reconstruction within recorded limits for',len(reconstruction),'camera snapshots; estimator not scored.')
    if not all(x['pass'] for x in reconstruction):
        print('Reconstruction limits failed; full measurements retained. Estimator remains unscored.')
        raise SystemExit(1)
