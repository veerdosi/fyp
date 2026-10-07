"""Sensor-only point correspondence prototype. No simulator or task imports."""
import cv2
import numpy as np


PARAMETERS = dict(window_pixels=21, pyramid_levels=3, iterations=30,
                  convergence_pixels=.01, minimum_eigenvalue=1e-4,
                  maximum_forward_backward_pixels=1.0,
                  maximum_world_jump_m=.08, initial_patch_std_min=5.0,
                  initial_patch_radius=3, minimum_depth_m=.001,
                  maximum_depth_m=10.0)


def world_point(pixel, depth, calibration):
    if not np.all(np.isfinite(pixel)):
        return None
    u, v = map(float, pixel)
    h, w = depth.shape
    x, y = int(round(u)), int(round(v))
    if not (0 <= x < w and 0 <= y < h):
        return None
    z = float(depth[y, x])
    if not np.isfinite(z) or not PARAMETERS['minimum_depth_m'] < z < PARAMETERS['maximum_depth_m']:
        return None
    optical = np.linalg.solve(np.asarray(calibration['intrinsic']), np.array([u, v, 1.])) * z
    return (np.asarray(calibration['camera_to_world']) @ np.r_[optical, 1.])[:3]


class PointTracker:
    def __init__(self, rgb, depth, calibration, pixels):
        self.gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        self.pixels = np.array(pixels, dtype=np.float32).reshape(-1, 1, 2)
        self.active = np.ones(len(pixels), dtype=bool)
        self.world = [world_point(p, depth, calibration) for p in pixels]
        self.loss_reason = [None] * len(pixels)
        radius = PARAMETERS['initial_patch_radius']
        h, w = self.gray.shape
        for i, (u, v) in enumerate(pixels):
            x, y = int(round(u)), int(round(v))
            patch = self.gray[max(0,y-radius):min(h,y+radius+1), max(0,x-radius):min(w,x+radius+1)]
            if self.world[i] is None or not patch.size or float(patch.std()) < PARAMETERS['initial_patch_std_min']:
                self.active[i] = False
                self.loss_reason[i] = 'invalid_initial_depth_or_texture'

    def update(self, rgb, depth, calibration):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        kwargs = dict(winSize=(PARAMETERS['window_pixels'],)*2,
                      maxLevel=PARAMETERS['pyramid_levels'],
                      criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                PARAMETERS['iterations'], PARAMETERS['convergence_pixels']),
                      minEigThreshold=PARAMETERS['minimum_eigenvalue'])
        following, valid, _ = cv2.calcOpticalFlowPyrLK(self.gray, gray, self.pixels, None, **kwargs)
        backward, reverse_valid, _ = cv2.calcOpticalFlowPyrLK(gray, self.gray, following, None, **kwargs)
        fb = np.linalg.norm(backward[:,0] - self.pixels[:,0], axis=1)
        result = []
        for i, pixel in enumerate(following[:,0]):
            point = world_point(pixel, depth, calibration)
            reason = None
            if not valid[i,0] or not reverse_valid[i,0] or not np.isfinite(fb[i]) or fb[i] > PARAMETERS['maximum_forward_backward_pixels']:
                reason = 'correspondence_inconsistent'
            elif point is None:
                reason = 'invalid_depth_or_outside_image'
            elif self.world[i] is not None and np.linalg.norm(point - self.world[i]) > PARAMETERS['maximum_world_jump_m']:
                reason = 'world_point_jump'
            if self.active[i] and reason:
                self.active[i] = False
                self.loss_reason[i] = reason
            accepted = bool(self.active[i])
            result.append(dict(accepted=accepted, pixel=pixel.tolist(),
                               world_xyz=point.tolist() if accepted else None,
                               forward_backward_pixels=float(fb[i]) if np.isfinite(fb[i]) else None,
                               loss_reason=self.loss_reason[i]))
            if accepted:
                self.world[i] = point
        self.pixels, self.gray = following, gray
        return result
