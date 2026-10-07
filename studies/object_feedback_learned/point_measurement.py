"""Causal RGB point tracker with public depth/calibration unprojection only."""
import hashlib
import time
import numpy as np
import torch
from cotracker.predictor import CoTrackerOnlinePredictor


def world_point(pixel, depth, calibration):
    if not np.all(np.isfinite(pixel)):
        return None
    u, v = map(float, pixel)
    h, w = depth.shape
    x, y = int(round(u)), int(round(v))
    if not (0 <= x < w and 0 <= y < h):
        return None
    z = float(depth[y, x])
    if not np.isfinite(z) or not .001 < z < 10:
        return None
    optical = np.linalg.solve(np.asarray(calibration['intrinsic']), [u, v, 1.]) * z
    return (np.asarray(calibration['camera_to_world']) @ np.r_[optical, 1.])[:3]


class OnlinePointMeasurement:
    def __init__(self, checkpoint):
        self.model = CoTrackerOnlinePredictor(checkpoint=str(checkpoint)).to('mps').eval()
        assert self.model.step == 8 and self.model.model.window_len == 16

    def tensor(self, frames):
        return torch.from_numpy(np.asarray(frames).copy()).permute(0,3,1,2)[None].float().to('mps')

    def seed(self, rgb, pixels):
        self.frames = [rgb.copy()]
        self.frame = 0
        self.last_endpoint = None
        self.query_count = len(pixels)
        queries = torch.tensor([[0.,float(u),float(v)] for u,v in pixels])[None].to('mps')
        torch.mps.synchronize()
        began = time.monotonic()
        self.model(self.tensor(self.frames),is_first_step=True,queries=queries,add_support_grid=True)
        torch.mps.synchronize()
        return time.monotonic()-began

    def update(self, rgb, depth, calibration, final=False):
        self.frame += 1
        self.frames.append(rgb.copy())
        due = self.frame >= 15 and (self.last_endpoint is None or self.frame-self.last_endpoint == 8 or final)
        if not due:
            return None, None
        start = 0 if self.last_endpoint is None else self.last_endpoint-7
        assert len(self.frames) == self.frame-start+1
        torch.mps.synchronize()
        began = time.monotonic()
        tracks, visible = self.model(self.tensor(self.frames),add_support_grid=True)
        assert tracks.shape[1] == self.frame+1 and visible.shape[1] == self.frame+1
        assert tracks.shape[2] == self.query_count
        pixels = tracks[0,self.frame].cpu().numpy()
        masks = visible[0,self.frame].cpu().numpy()
        torch.mps.synchronize()
        seconds = time.monotonic()-began
        assert np.all(np.isfinite(pixels))
        results = []
        for pixel, mask in zip(pixels,masks):
            point = world_point(pixel,depth,calibration)
            accepted = bool(mask) and point is not None
            results.append(dict(pixel=pixel.tolist(),model_visible=bool(mask),accepted=accepted,
                world_xyz=point.tolist() if accepted else None,
                loss_reason=None if accepted else 'model_not_visible' if not mask else 'invalid_public_depth'))
        log = dict(first_input_frame=start,last_input_frame=self.frame,output_frame=self.frame,
            bootstrap=self.last_endpoint is None,partial_tail=self.last_endpoint is not None and self.frame-self.last_endpoint<8,
            synchronized_seconds=seconds,tracks_shape=list(tracks.shape),no_future_inputs=True,
            rgb_chunk_sha256=hashlib.sha256(np.asarray(self.frames).tobytes()).hexdigest(),
            observed_driver_memory_bytes=int(torch.mps.driver_allocated_memory()),outputs=results)
        self.last_endpoint = self.frame
        self.frames = self.frames[-8:]
        return results, log
