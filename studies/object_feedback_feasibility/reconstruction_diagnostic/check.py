"""Compare saved-state rendering and action replay at the first cohort snapshot."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'src'))
from fyp.runtime import make_env, sensor_images
from robosuite.utils.camera_utils import get_camera_extrinsic_matrix

segment = json.loads((HERE.parent/'cohort.json').read_text())['streams'][0]
run = ROOT/'runs'/segment['episode']
config = json.loads((run/'config.json').read_text())
saved = np.load(run/'trajectory.npz')
folder = run/f"public/obs_{segment['observation_id']:04d}"
cal = json.loads((folder/'calibration.json').read_text())
results = {}
for mode in ['saved_state_render', 'recorded_action_replay', 'native_reset_action_replay']:
    env, obs, _ = make_env(**{k: config[k] for k in ['task','suite','seed','state_index','size']})
    errors = []
    if mode == 'saved_state_render':
        obs = env.set_init_state(saved['states'][segment['start_step']-1])
    else:
        if mode == 'recorded_action_replay':
            obs = env.set_init_state(saved['initial'])
        else:
            assert np.array_equal(env.get_sim_state(),saved['initial'])
        for i, action in enumerate(saved['actions'][:segment['start_step']]):
            obs, _, _, _ = env.step(action)
            errors.append(float(np.max(np.abs(env.get_sim_state()-saved['states'][i]))))
    sensors = sensor_images(env,obs)
    checks = {}
    for camera, (rgb,depth) in sensors.items():
        old_rgb = np.asarray(Image.open(folder/(camera+'.png')))
        old_depth = np.load(folder/(camera+'_depth_m.npy'))
        checks[camera] = dict(rgb_exact=np.array_equal(rgb,old_rgb),
            changed_rgb_pixels=int(np.count_nonzero(np.any(rgb != old_rgb,axis=2))),
            depth_max_error_m=float(np.max(np.abs(depth-old_depth))),
            calibration_max_error=float(np.max(np.abs(get_camera_extrinsic_matrix(env.sim,camera)-cal[camera]['camera_to_world']))))
    results[mode] = dict(snapshot_checks=checks, max_state_error=max(errors,default=0))
    env.close()
(HERE/'result.json').write_text(json.dumps(dict(episode=run.name,step=segment['start_step'],
    actual_model_requests=0,results=results),indent=2))
print(json.dumps(results,indent=2))
