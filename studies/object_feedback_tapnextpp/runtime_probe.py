"""One bounded causal compatibility probe; inputs are public RGB/query pixels."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def worker(device, folder):
    import numpy as np
    import torch
    import torchvision
    import einops
    sys.path.insert(0, str(ROOT / 'vendor/tapnet'))
    from tapnet.tapnextpp.votsp2026.model import TAPNextPP

    protocol = json.loads((HERE / 'probe_protocol.json').read_text())
    assert not os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')
    assert torch.__version__ == protocol['dependencies']['torch']
    assert torchvision.__version__ == protocol['dependencies']['torchvision']
    assert einops.__version__ == protocol['dependencies']['einops']
    assert sha(Path(__file__)) == protocol['probe_source_sha256']
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT / name) == expected, name
    archive = ROOT / protocol['input_path']
    checkpoint = ROOT / protocol['checkpoint_path']
    assert sha(archive) == protocol['input_sha256']
    assert sha(checkpoint) == protocol['checkpoint_sha256']
    # Reuse the official support-grid functions verbatim without importing VOT.
    source = ROOT / 'vendor/tapnet/tapnet/tapnextpp/votsp2026/tracker.py'
    nodes = [n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef)
             and n.name in {'grid_support_points', 'local_support_points'}]
    assert len(nodes) == 2
    scope = {'np': np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), scope)
    torch.manual_seed(0)
    began = time.monotonic()
    save(folder / 'progress.json', {'phase': 'loading', 'device': device})
    model = TAPNextPP.from_checkpoint(checkpoint, device=device, input_resolution=512,
                                      half_precision=False, compile_model=False)
    if device == 'mps':
        torch.mps.synchronize()
    loading = time.monotonic() - began
    data = np.load(archive)
    records = []
    with (folder / 'outputs.jsonl').open('w') as outputs:
        for camera in protocol['cameras']:
            frames = data[camera]
            assert len(frames) == protocol['frames_per_camera']
            points = data[camera + '_queries'][:, 1:].copy()
            h, w = frames[0].shape[:2]
            support = scope['local_support_points'](points, 64, 32*w/512, 32*h/512, w, h)
            queries = np.concatenate([points, support], axis=0)
            state = None
            for index, rgb in enumerate(frames):
                tick = time.monotonic()
                if index == 0:
                    xy, visible, state = model.track_frame(rgb[..., ::-1].copy(),
                                query_points_xy=queries, autocast=False)
                else:
                    xy, visible, state = model.track_frame(rgb[..., ::-1].copy(),
                                state=state, autocast=False)
                if device == 'mps':
                    torch.mps.synchronize()
                elapsed = time.monotonic() - tick
                assert state.step == index + 1
                assert xy.shape == (len(queries), 2) and visible.shape == (len(queries),)
                assert np.all(np.isfinite(xy))
                record = dict(camera=camera, output_frame=index, last_input_frame=index,
                    no_future_inputs=True, state_step=state.step, seconds=elapsed,
                    real_queries=len(points), support_queries=len(support),
                    pixel=xy[:len(points)].tolist(), visible=visible[:len(points)].tolist())
                if device == 'mps':
                    record.update(allocated_memory_bytes=int(torch.mps.current_allocated_memory()),
                                  driver_memory_bytes=int(torch.mps.driver_allocated_memory()))
                records.append(record)
                outputs.write(json.dumps(record, allow_nan=False) + '\n')
                outputs.flush()
                save(folder / 'progress.json', dict(phase='tracking', device=device,
                     completed_frames=len(records), last_camera=camera, last_frame=index,
                     elapsed_seconds=time.monotonic()-began))
                if index % 8 == 0:
                    print(camera, index, round(elapsed, 3), 'seconds', flush=True)
            del state
    timings = {camera: dict(first_frame_seconds=next(r['seconds'] for r in records if r['camera']==camera),
                   subsequent_frame_p95_seconds=float(np.percentile([r['seconds'] for r in records
                             if r['camera']==camera and r['output_frame']>0], 95)))
               for camera in protocol['cameras']}
    save(folder / 'result.json', dict(completed=True, device=device, loading_seconds=loading,
        total_seconds=time.monotonic()-began, frames=len(records), timings=timings,
        observed_driver_peak_bytes=max((r.get('driver_memory_bytes', 0) for r in records)),
        causal_outputs_checked=True, actual_astra_requests=0,
        scope='Public-prefix compatibility/runtime only; no geometric accuracy or task efficacy claim.'))


def run():
    protocol = json.loads((HERE / 'probe_protocol.json').read_text())
    assert sha(Path(__file__)) == protocol['probe_source_sha256']
    assert sha(ROOT / protocol['decision']) == protocol['decision_sha256']
    attempts = []
    for device in ['mps', 'cpu']:
        folder = HERE / ('probe_' + device)
        folder.mkdir()  # Preserve prior runs; never overwrite an existing attempt.
        save(folder / 'configuration.json', dict(protocol=protocol,
             protocol_sha256=sha(HERE / 'probe_protocol.json'), device=device,
             reproduce='.venv/bin/python studies/object_feedback_tapnextpp/runtime_probe.py'))
        env = os.environ.copy()
        env.pop('PYTORCH_ENABLE_MPS_FALLBACK', None)
        tick = time.monotonic()
        with (folder / 'stdout.log').open('w') as out, (folder / 'stderr.log').open('w') as err:
            try:
                completed = subprocess.run([sys.executable, str(Path(__file__)), '--worker', device, str(folder)],
                    stdout=out, stderr=err, env=env, timeout=protocol['per_device_timeout_seconds'])
                status = dict(device=device, exit_code=completed.returncode, timed_out=False)
            except subprocess.TimeoutExpired:
                status = dict(device=device, exit_code=None, timed_out=True)
        status['host_seconds'] = time.monotonic()-tick
        result_path = folder / 'result.json'
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        status['completed'] = result.get('completed', False)
        save(folder / 'execution.json', status)
        attempts.append(status)
        save(HERE / 'runtime_result.json', dict(attempts=attempts, actual_astra_requests=0,
            completed_device=device if status['completed'] else None))
        print(json.dumps(status), flush=True)
        if status['completed'] or status['timed_out'] or device == 'cpu':
            break
        # A CPU attempt is permitted only for an explicit unsupported MPS operation.
        failure = (folder / 'stderr.log').read_text()
        unsupported = ('NotImplementedError' in failure and 'MPS' in failure)
        unsupported |= ('not supported' in failure.lower() and 'mps' in failure.lower())
        if not unsupported:
            break


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        folder = Path(sys.argv[3])
        try:
            worker(sys.argv[2], folder)
        except Exception as exc:
            save(folder / 'error.json', dict(type=type(exc).__name__, message=str(exc),
                traceback=traceback.format_exc(), actual_astra_requests=0))
            raise
    else:
        run()
