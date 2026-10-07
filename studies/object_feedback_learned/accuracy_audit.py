"""Causal endpoint audit on every original query; private geometry scores only."""
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'vendor/co-tracker'))
sys.path.append(str(ROOT/'studies/object_feedback_feasibility'))
from fyp.runtime import make_env, sensor_images
from robosuite.utils.camera_utils import get_camera_extrinsic_matrix, get_camera_intrinsic_matrix
from point_measurement import OnlinePointMeasurement
from private_reference import reference, truth, summarize
from camera_reference import CameraReferenceCapture


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (HERE/name).write_text(json.dumps(data,indent=2)+'\n')


def main():
    protocol = json.loads((HERE/'accuracy_protocol.json').read_text())
    for path, expected in protocol['source_hashes'].items():
        assert sha(ROOT/path) == expected, path
    checkpoint = ROOT/'vendor/checkpoints/scaled_online.pth'
    assert sha(checkpoint) == protocol['checkpoint_sha256']
    cohort = json.loads((ROOT/'studies/object_feedback_feasibility/cohort.json').read_text())
    assert cohort['query_count'] == cohort['retained_query_count'] == 212
    torch.manual_seed(0)
    assert torch.backends.mps.is_available()
    began = time.monotonic()
    models = {camera:OnlinePointMeasurement(checkpoint) for camera in ['agentview','robot0_eye_in_hand']}
    torch.mps.synchronize()
    loading_seconds = time.monotonic()-began
    rows, ledger, initial_points, reconstruction, replay_checks, updates, seeds = [], [], [], [], [], [], []
    streams = cohort['streams']
    for trial in cohort['episodes']:
        run = ROOT/'runs'/trial['episode']
        assert sha(run/'commands.jsonl') == trial['command_sha256']
        assert sha(run/'trajectory.npz') == trial['trajectory_sha256']
        config = json.loads((run/'config.json').read_text())
        saved = np.load(run/'trajectory.npz')
        env, obs, initial = make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
        assert np.array_equal(initial,saved['initial'])
        segments = [s for s in streams if s['episode']==run.name]
        capture = CameraReferenceCapture(env,segments,reference,truth)
        active = []
        max_state_error = 0.
        for index, action in enumerate(saved['actions']):
            capture.step = index+1
            obs, _, _, _ = env.step(action)
            step = index+1
            error = float(np.max(np.abs(env.get_sim_state()-saved['states'][index])))
            max_state_error = max(max_state_error,error)
            assert error == 0., 'Replay diverged'
            starting = [s for s in segments if s['start_step']==step]
            if not active and not starting:
                continue
            sensors = sensor_images(env,obs)
            calibration = {camera:dict(intrinsic=get_camera_intrinsic_matrix(env.sim,camera,*rgb.shape[:2]).tolist(),
                camera_to_world=get_camera_extrinsic_matrix(env.sim,camera).tolist()) for camera,(rgb,depth) in sensors.items()}
            for segment, points, references in active:
                for camera, pts in points.items():
                    rgb,depth = sensors[camera]
                    estimator = models[camera]
                    output,log = estimator.update(rgb,depth,calibration[camera],final=step==segment['end_step'])
                    if log is not None:
                        updates.append(dict(episode=run.name,observation_id=segment['observation_id'],camera=camera,step=step,**log))
                    for i,(p,ref) in enumerate(zip(pts,references[camera])):
                        sampled = capture.measurements[camera]
                        measured = sampled['points'][(p['query_decision'],p['pixel_index'])]
                        identity = dict(episode=run.name,paired_state=segment['paired_state'],condition=segment['condition'],
                            camera=camera,motion_type=segment['motion_type'],query_decision=p['query_decision'],
                            pixel_index=p['pixel_index'],step=step,relative_frame=step-segment['start_step'])
                        ledger.append(dict(**identity,fresh=output is not None,
                            last_endpoint_age_steps=None if estimator.last_endpoint is None else estimator.frame-estimator.last_endpoint,
                            reference_visible=measured['visible'],current_world_xyz=output[i]['world_xyz'] if output is not None else None))
                        if output is None:
                            continue
                        result = output[i]
                        expected = capture.current_world(ref)
                        error = float(np.linalg.norm(np.asarray(result['world_xyz'])-expected)) if expected is not None and result['accepted'] else None
                        image_error = float(np.linalg.norm(np.asarray(result['world_xyz'])-measured['point'])) if measured['point'] is not None and result['accepted'] else None
                        rows.append(dict(**identity,reference_visible=measured['visible'],world_error_m=error,
                            image_time_error_m=image_error,reference_body=ref['body_name'] if ref else 'unknown',
                            camera_age_seconds=float(env.sim.data.time-sampled['time']),**result))
            ended = [a for a in active if a[0]['end_step']==step]
            active = [a for a in active if a[0]['end_step']>step]
            if ended:
                save('accuracy_progress.json',dict(episodes_complete=len(replay_checks),streams_complete=sum(s['end_step']<=step for s in segments),
                    current_episode=run.name,current_step=step,endpoint_samples=len(rows),updates=len(updates),wall_seconds=time.monotonic()-began))
                print(run.name,'completed stream',step,'updates',len(updates),flush=True)
            for segment in starting:
                assert not active, 'Overlapping stream needs independent model state'
                folder = run/f"public/obs_{segment['observation_id']:04d}"
                original_cal = json.loads((folder/'calibration.json').read_text())
                points, references = {}, {}
                for camera in sorted(set(p['camera'] for p in segment['points'])):
                    rgb = np.asarray(Image.open(folder/(camera+'.png')))
                    depth = np.load(folder/(camera+'_depth_m.npy'))
                    replay_rgb,replay_depth = sensors[camera]
                    check = dict(episode=run.name,observation_id=segment['observation_id'],camera=camera,
                        rgb_exact=np.array_equal(rgb,replay_rgb),depth_exact=np.array_equal(depth,replay_depth),
                        calibration_exact=all(np.array_equal(original_cal[camera][k],calibration[camera][k]) for k in ['intrinsic','camera_to_world']))
                    reconstruction.append(check)
                    assert all(check[k] for k in ['rgb_exact','depth_exact','calibration_exact']), check
                    pts = [p for p in segment['points'] if p['camera']==camera]
                    refs = [capture.seeds[(p['query_decision'],p['pixel_index'])] for p in pts]
                    seconds = models[camera].seed(rgb,[[p['u'],p['v']] for p in pts])
                    seeds.append(dict(episode=run.name,observation_id=segment['observation_id'],camera=camera,seed_seconds=seconds,
                        rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),pixels=[[p['u'],p['v']] for p in pts]))
                    capture.activate(camera,pts,refs)
                    points[camera],references[camera] = pts,refs
                    for p,ref in zip(pts,refs):
                        initial_points.append(dict(episode=run.name,**p,reference_available=ref is not None,
                            reference_body=ref['body_name'] if ref else None,semantic_correctness='Not inferred from surface correspondence'))
                active.append((segment,points,references))
        replay_checks.append(dict(episode=run.name,steps=len(saved['actions']),max_state_absolute_error=max_state_error))
        env.close()
        # Save completed evidence after each episode; never discard an outcome.
        for name,items in [('endpoint_samples.jsonl.gz',rows),('availability.jsonl.gz',ledger)]:
            with gzip.open(HERE/name,'wt') as handle:
                for item in items:
                    handle.write(json.dumps(item)+'\n')
        save('accuracy_updates.json',dict(updates=updates,seeds=seeds))
        save('accuracy_reconstruction.json',dict(checks=reconstruction,replay_checks=replay_checks))
    groups = {key:{str(value):summarize([r for r in rows if r[key]==value]) for value in sorted(set(r[key] for r in rows))}
        for key in ['camera','motion_type','paired_state','condition','reference_body']}
    expected_ledger = sum(len(s['points'])*(s['end_step']-s['start_step']) for s in streams)
    def endpoints(n):
        out=list(range(15,n+1,8))
        if out and out[-1]!=n:
            out.append(n)
        return out
    expected_rows = sum(len(s['points'])*len(endpoints(s['end_step']-s['start_step'])) for s in streams)
    expected_updates = sum(len(set(p['camera'] for p in s['points']))*len(endpoints(s['end_step']-s['start_step'])) for s in streams)
    assert len(ledger)==expected_ledger and len(rows)==expected_rows and len(updates)==expected_updates
    assert len(initial_points)==212 and len(reconstruction)==49 and len(replay_checks)==6
    result = dict(scope='Observed-trace development accuracy at causal endpoints; periodic interface, no task benefit claim.',
        protocol=protocol,overall=summarize(rows),groups=groups,initial_queries=initial_points,
        availability=dict(motion_query_frames=len(ledger),fresh_query_frames=len(rows),fresh_fraction=len(rows)/len(ledger),
            bootstrap_acquisition_seconds=.75,no_fabricated_between_update_points=True),
        loading_seconds=loading_seconds,tracking_seconds=sum(u['synchronized_seconds'] for u in updates),
        bootstrap_call_p95_seconds=float(np.percentile([u['synchronized_seconds'] for u in updates if u['bootstrap']],95)),
        steady_call_p95_seconds=float(np.percentile([u['synchronized_seconds'] for u in updates if not u['bootstrap'] and not u['partial_tail']],95)),
        total_wall_seconds=time.monotonic()-began,local_tracker_forward_calls=len(updates),actual_astra_requests=0,
        expected_endpoint_samples=expected_rows,expected_availability_samples=expected_ledger,
        all_actions_replayed_exactly=True,all_query_sensors_bit_exact=True)
    save('accuracy_result.json',result)
    print(json.dumps(result['overall'],indent=2),flush=True)


if __name__ == '__main__':
    main()
