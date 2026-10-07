"""Causal two-camera CoTracker3 runtime probe; consumes RGB/pixel inputs only."""
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'vendor/co-tracker'))
from cotracker.predictor import CoTrackerOnlinePredictor

protocol = json.loads((HERE/'probe_protocol.json').read_text())
inputs = HERE/'probe_inputs.npz'
checkpoint = ROOT/'vendor/checkpoints/scaled_online.pth'
assert hashlib.sha256(inputs.read_bytes()).hexdigest() == protocol['input_sha256']
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == protocol['checkpoint_sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == protocol['runtime_source_sha256']
for file,expected in protocol['third_party_source_hashes'].items():
    assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest() == expected
assert torch.backends.mps.is_available()
device = 'mps'
torch.manual_seed(0)
data = np.load(inputs)
cameras = ['agentview','robot0_eye_in_hand']
t0 = time.monotonic()
models = {camera:CoTrackerOnlinePredictor(checkpoint=str(checkpoint)).to(device).eval() for camera in cameras}
torch.mps.synchronize()
loading_seconds = time.monotonic()-t0
for camera,model in models.items():
    assert model.step == 8 and model.model.window_len == 16
    init = torch.from_numpy(data[camera][:1].copy()).permute(0,3,1,2)[None].float().to(device)
    queries = torch.from_numpy(data[camera+'_queries'].copy())[None].to(device)
    model(init,is_first_step=True,queries=queries,add_support_grid=True)
torch.mps.synchronize()
records = []
count = len(data[cameras[0]])
# A 16-frame causal bootstrap, followed by eight new frames per update.
endpoints = list(range(15,count,8))
if endpoints[-1] != count-1:
    endpoints.append(count-1)
for index,end in enumerate(endpoints):
    start = 0 if index==0 else endpoints[index-1]-7
    torch.mps.synchronize()
    began = time.monotonic()
    predictions = {}
    for camera,model in models.items():
        chunk = torch.from_numpy(data[camera][start:end+1].copy()).permute(0,3,1,2)[None].float().to(device)
        tracks,visible = model(chunk,add_support_grid=True)
        assert tracks.shape[1] == end+1 and visible.shape[1] == end+1
        assert tracks.shape[2] == len(data[camera+'_queries'])
        point = tracks[0,end].cpu().numpy()
        mask = visible[0,end].cpu().numpy()
        assert np.all(np.isfinite(point))
        predictions[camera] = dict(tracks_shape=list(tracks.shape),visibility_shape=list(visible.shape),
            latest_pixel=point.tolist(),latest_visible=mask.tolist(),
            output_frame=end,last_input_frame=end,no_future_inputs=True)
    torch.mps.synchronize()
    records.append(dict(update=index,first_input_frame=start,last_input_frame=end,
        latest_frame_seconds=end/20,combined_two_camera_seconds=time.monotonic()-began,
        bootstrap=index==0,partial_tail=index>0 and end-endpoints[index-1]<8,
        observed_allocated_memory_bytes=int(torch.mps.current_allocated_memory()),
        observed_driver_memory_bytes=int(torch.mps.driver_allocated_memory()),predictions=predictions))
    (HERE/'runtime_progress.json').write_text(json.dumps(records,indent=2)+'\n')
    print('endpoint',end,'combined seconds',records[-1]['combined_two_camera_seconds'],flush=True)
steady = [r['combined_two_camera_seconds'] for r in records if not r['bootstrap'] and not r['partial_tail']]
p95 = float(np.percentile(steady,95))
result = dict(device=device,torch_version=torch.__version__,protocol=protocol,loading_seconds=loading_seconds,
    bootstrap_acquisition_seconds=15/20,bootstrap_compute_seconds=records[0]['combined_two_camera_seconds'],
    steady_updates=len(steady),steady_two_camera_p95_seconds=p95,
    update_acquisition_seconds=.4,runtime_gate_pass=p95 <= .4,causal_output_checks_pass=True,
    actual_astra_inference_requests=0,updates=records,
    scope='Chronological-prefix compatibility/causality/runtime probe; no geometric accuracy or robot-task success claim.')
(HERE/'runtime_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['steady_two_camera_p95_seconds','runtime_gate_pass','causal_output_checks_pass']},indent=2))
