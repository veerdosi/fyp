"""Score one frozen public-depth estimator on cached causal tracker outputs."""
import ast
from collections import Counter
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.append(str(ROOT / 'studies/object_feedback_feasibility'))
from fyp.runtime import make_env, sensor_images
from robosuite.utils.camera_utils import get_camera_extrinsic_matrix, get_camera_intrinsic_matrix
from camera_reference import CameraReferenceCapture
from measurement import Measurement, nearest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load_rows(path):
    with gzip.open(path, 'rt') as handle:
        return [json.loads(line) for line in handle]


def identity(row):
    return (row['episode'], row['camera'], row['query_decision'], row['pixel_index'], row['step'])


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    for path, expected in protocol['source_hashes'].items():
        assert sha(ROOT / path) == expected, path
    assert protocol['primary']['patch_size'] == 3
    attempt = 1
    while (HERE / f'attempt_{attempt:03d}').exists():
        attempt += 1
    folder = HERE / f'attempt_{attempt:03d}'
    folder.mkdir()
    save(folder / 'configuration.json', dict(protocol=protocol,
         protocol_sha256=sha(HERE / 'protocol.json'),
         code_hashes={name: sha(HERE / name) for name in ['audit.py', 'measurement.py']},
         reproduce='.venv/bin/python studies/object_feedback_depth/audit.py',
         actual_astra_requests=0, local_tracker_forward_calls=0))
    # Reuse verified scoring functions without importing or loading a tracker.
    source = ROOT / 'studies/object_feedback_learned/private_reference.py'
    names = {'ray_body', 'reference', 'truth', 'summarize'}
    functions = [node for node in ast.parse(source.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(functions) == 4
    def world_point(pixel, depth, calibration):
        output = nearest(pixel, depth, calibration, True)
        return np.asarray(output['world_xyz']) if output['accepted'] else None
    scope = dict(np=np, mujoco=mujoco, world_point=world_point)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), scope)
    cohort = json.loads((ROOT / 'studies/object_feedback_feasibility/cohort.json').read_text())
    original = load_rows(ROOT / 'studies/object_feedback_learned/endpoint_samples.jsonl.gz')
    cached = {identity(row): row for row in original}
    assert len(cached) == len(original) == protocol['cohort']['endpoints']
    update_logs = json.loads((ROOT / 'studies/object_feedback_learned/accuracy_updates.json').read_text())['updates']
    update_by_key = {(u['episode'], u['observation_id'], u['camera'], u['step']): u for u in update_logs}
    rows, replay_checks, camera_checks, input_manifests, calculation_seconds = [], [], [], [], []
    consumed, seed_count, stream_count = set(), 0, 0
    began = time.monotonic()
    variants = ['original_nearest_depth', 'local_support_median_only', 'primary']
    for trial in cohort['episodes']:
        run = ROOT / 'runs' / trial['episode']
        assert sha(run / 'commands.jsonl') == trial['command_sha256']
        assert sha(run / 'trajectory.npz') == trial['trajectory_sha256']
        config = json.loads((run / 'config.json').read_text())
        saved = np.load(run / 'trajectory.npz')
        env, obs, initial = make_env(**{k: config[k] for k in
                                      ['task', 'suite', 'seed', 'state_index', 'size']})
        assert np.array_equal(initial, saved['initial'])
        segments = [s for s in cohort['streams'] if s['episode'] == run.name]
        capture = CameraReferenceCapture(env, segments, scope['reference'], scope['truth'])
        active = []
        max_state_error = 0.
        for index, action in enumerate(saved['actions']):
            step = index + 1
            capture.step = step
            obs, _, _, _ = env.step(action)
            error = float(np.max(np.abs(env.get_sim_state() - saved['states'][index])))
            max_state_error = max(max_state_error, error)
            assert error == 0., 'Replay diverged'
            starting = [s for s in segments if s['start_step'] == step]
            due = [a for a in active if any(identity(dict(episode=run.name, camera=camera,
                    query_decision=p['query_decision'], pixel_index=p['pixel_index'], step=step)) in cached
                    for camera, pts in a[1].items() for p in pts)]
            if not due and not starting:
                continue
            sensors = sensor_images(env, obs)
            calibration = {camera: dict(intrinsic=get_camera_intrinsic_matrix(env.sim, camera, *rgb.shape[:2]).tolist(),
                camera_to_world=get_camera_extrinsic_matrix(env.sim, camera).tolist())
                for camera, (rgb, depth) in sensors.items()}
            if due:
                input_manifests.append(dict(episode=run.name, step=step,
                    cameras={camera: dict(rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                        depth_sha256=hashlib.sha256(depth.tobytes()).hexdigest(), calibration=calibration[camera])
                        for camera, (rgb, depth) in sensors.items()}))
            for segment, points, references, estimators in due:
                for camera, pts in points.items():
                    other = 'robot0_eye_in_hand' if camera == 'agentview' else 'agentview'
                    for i, (point, ref) in enumerate(zip(pts, references[camera])):
                        key = identity(dict(episode=run.name, camera=camera, query_decision=point['query_decision'],
                                            pixel_index=point['pixel_index'], step=step))
                        if key not in cached:
                            continue
                        raw = cached[key]
                        update = update_by_key[(run.name, segment['observation_id'], camera, step)]
                        assert update['no_future_inputs']
                        assert update['output_frame'] == update['last_input_frame'] == raw['relative_frame']
                        assert update['outputs'][i]['pixel'] == raw['pixel']
                        assert update['outputs'][i]['model_visible'] == raw['model_visible']
                        assert key not in consumed
                        consumed.add(key)
                        rgb, depth = sensors[camera]
                        tick = time.perf_counter()
                        outputs = estimators[camera][i].update(raw['pixel'], raw['model_visible'], depth,
                            calibration[camera], sensors[other][1], calibration[other], step / 20.)
                        calculation_seconds.append(time.perf_counter() - tick)
                        assert outputs[0]['accepted'] == raw['accepted']
                        assert outputs[0]['world_xyz'] == raw['world_xyz'], 'Original public unprojection differs'
                        sampled = capture.measurements[camera]
                        measured = sampled['points'][(point['query_decision'], point['pixel_index'])]
                        assert measured['visible'] == raw['reference_visible']
                        expected = capture.current_world(ref)
                        base = {k: raw[k] for k in ['episode', 'paired_state', 'condition', 'camera',
                                'motion_type', 'query_decision', 'pixel_index', 'step', 'relative_frame']}
                        for name, output in zip(variants, outputs):
                            candidate = np.asarray(output['world_xyz']) if output['accepted'] else None
                            metric_error = float(np.linalg.norm(candidate - expected)) if expected is not None and candidate is not None else None
                            image_error = float(np.linalg.norm(candidate - measured['point'])) if measured['point'] is not None and candidate is not None else None
                            if name == variants[0]:
                                assert metric_error == raw['world_error_m']
                                assert image_error == raw['image_time_error_m']
                            rows.append(dict(**base, variant=name, pixel=raw['pixel'],
                                reference_visible=measured['visible'], world_error_m=metric_error,
                                image_time_error_m=image_error, reference_body=raw['reference_body'],
                                camera_age_seconds=float(env.sim.data.time - sampled['time']), **output))
            ended = [a for a in active if a[0]['end_step'] == step]
            stream_count += len(ended)
            active = [a for a in active if a[0]['end_step'] > step]
            for segment in starting:
                assert not active, 'Overlapping streams'
                public = run / f"public/obs_{segment['observation_id']:04d}"
                original_calibration = json.loads((public / 'calibration.json').read_text())
                points, references, estimators = {}, {}, {}
                for camera in sorted(set(p['camera'] for p in segment['points'])):
                    rgb, depth = sensors[camera]
                    check = dict(episode=run.name, observation_id=segment['observation_id'], camera=camera,
                        rgb_exact=np.array_equal(rgb, np.asarray(Image.open(public / (camera + '.png')))),
                        depth_exact=np.array_equal(depth, np.load(public / (camera + '_depth_m.npy'))),
                        calibration_exact=all(np.array_equal(original_calibration[camera][k], calibration[camera][k])
                                              for k in ['intrinsic', 'camera_to_world']))
                    assert all(check[k] for k in ['rgb_exact', 'depth_exact', 'calibration_exact'])
                    camera_checks.append(check)
                    pts = [p for p in segment['points'] if p['camera'] == camera]
                    refs = [capture.seeds[(p['query_decision'], p['pixel_index'])] for p in pts]
                    capture.activate(camera, pts, refs)
                    points[camera], references[camera] = pts, refs
                    estimators[camera] = [Measurement(protocol['primary'], p['world_xyz'], step / 20.) for p in pts]
                    seed_count += len(pts)
                active.append((segment, points, references, estimators))
            if ended:
                progress = dict(current_episode=run.name, current_step=step, streams_complete=stream_count,
                                endpoints_complete=len(consumed), wall_seconds=time.monotonic() - began)
                save(folder / 'progress.json', progress)
                print(json.dumps(progress), flush=True)
        assert not active
        replay_checks.append(dict(episode=run.name, steps=len(saved['actions']), max_state_error=max_state_error))
        env.close()
        with gzip.open(folder / 'endpoint_samples.jsonl.gz', 'wt') as handle:
            for row in rows:
                handle.write(json.dumps(row, allow_nan=False) + '\n')
        save(folder / 'reconstruction.json', dict(replay_checks=replay_checks, camera_checks=camera_checks))
        save(folder / 'public_input_manifests.json', input_manifests)
    assert consumed == set(cached)
    assert seed_count == 212 and stream_count == 35 and len(camera_checks) == 49
    assert len(rows) == 2757 * 3 and len(replay_checks) == 6
    groups = {}
    for variant in variants:
        selected = [r for r in rows if r['variant'] == variant]
        by_group = {key: {str(value): scope['summarize']([r for r in selected if r[key] == value])
                    for value in sorted(set(r[key] for r in selected))}
                    for key in ['camera', 'paired_state', 'motion_type', 'condition']}
        overall = scope['summarize'](selected)
        groups[variant] = dict(overall=overall, groups=by_group,
            required_gates_pass=overall['gate_pass'] and all(
                g['gate_pass'] for key in ['camera', 'paired_state'] for g in by_group[key].values()),
            rejection_reasons=dict(Counter(r['loss_reason'] for r in selected if not r['accepted'])),
            cross_camera_status=dict(Counter(r.get('cross_camera_status', 'not_checked') for r in selected)))
    result = dict(protocol_sha256=sha(HERE / 'protocol.json'), configuration='configuration.json',
        variants=groups, queries=seed_count, streams=stream_count, endpoints=len(consumed),
        original_baseline_same_samples_exact=True, all_actions_states_exact=True,
        all_original_query_sensors_exact=True, causal_cache_outputs_verified=True,
        actual_astra_requests=0, local_tracker_forward_calls=0,
        measurement_three_variants_seconds=sum(calculation_seconds),
        per_point_three_variant_p95_seconds=float(np.percentile(calculation_seconds, 95)),
        total_wall_seconds=time.monotonic() - began,
        availability_scope='Original frozen 22739-frame ledger unchanged; no fresh measurements invented between endpoints.',
        interpretation_scope='Correlated observed-trace development measurements, not held-out robot outcomes.',
        reproduce='.venv/bin/python studies/object_feedback_depth/audit.py')
    save(folder / 'result.json', result)
    save(HERE / 'latest.json', dict(attempt=folder.name, completed=True, result=str(folder / 'result.json')))
    print(json.dumps({v: groups[v]['overall'] for v in variants}, indent=2), flush=True)


if __name__ == '__main__':
    main()
