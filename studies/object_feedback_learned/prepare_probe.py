"""Reconstruct the predefined chronological RGB-only runtime probe."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.runtime import make_env, sensor_images

segment = json.loads((ROOT/'studies/object_feedback_feasibility/cohort.json').read_text())['streams'][0]
run = ROOT/'runs'/segment['episode']
config = json.loads((run/'config.json').read_text())
saved = np.load(run/'trajectory.npz')
start, end = segment['start_step'],segment['start_step']+64
assert end <= segment['end_step']
env, obs, initial = make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
assert np.array_equal(initial,saved['initial'])
frames = {camera:[] for camera in ['agentview','robot0_eye_in_hand']}
max_error = 0.
for index,action in enumerate(saved['actions'][:end]):
    obs, _, _, _ = env.step(action)
    max_error = max(max_error,float(np.max(np.abs(env.get_sim_state()-saved['states'][index]))))
    if index+1 < start:
        continue
    sensors = sensor_images(env,obs)
    for camera in frames:
        rgb = sensors[camera][0]
        if index+1 == start:
            original = np.asarray(Image.open(run/f"public/obs_{segment['observation_id']:04d}/{camera}.png"))
            assert np.array_equal(rgb,original)
        frames[camera].append(rgb)
env.close()
assert max_error == 0
queries = {camera:np.asarray([[0,p['u'],p['v']] for p in segment['points'] if p['camera']==camera],dtype=np.float32)
           for camera in frames}
np.savez_compressed(HERE/'probe_inputs.npz',**{camera:np.stack(values) for camera,values in frames.items()},
                    **{camera+'_queries':points for camera,points in queries.items()})
manifest = dict(episode=run.name,source_trajectory_sha256=hashlib.sha256((run/'trajectory.npz').read_bytes()).hexdigest(),
    source_commands_sha256=hashlib.sha256((run/'commands.jsonl').read_bytes()).hexdigest(),
    observation_id=segment['observation_id'],query_step=start,last_step=end,frames_per_camera=65,
    queries_by_camera={k:len(v) for k,v in queries.items()},max_state_absolute_error=max_error,
    query_rgb_exact=True,actual_model_inference_requests=0,
    probe_inputs_sha256=hashlib.sha256((HERE/'probe_inputs.npz').read_bytes()).hexdigest(),
    preparation_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    input_boundary='Probe archive contains only reconstructed RGB and original public query pixels.')
(HERE/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
