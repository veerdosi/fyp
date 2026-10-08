"""Public-data-only depth association and uncertainty, using frozen parameters."""
import numpy as np


def unproject(pixel, depth_m, calibration):
    optical = np.linalg.solve(np.asarray(calibration['intrinsic']), [*pixel, 1.]) * depth_m
    return (np.asarray(calibration['camera_to_world']) @ np.r_[optical, 1.])[:3]


def nearest(pixel, depth, calibration, visible):
    if not visible:
        return dict(accepted=False, world_xyz=None, loss_reason='model_not_visible')
    if not np.all(np.isfinite(pixel)):
        return dict(accepted=False, world_xyz=None, loss_reason='invalid_pixel')
    x, y = [int(round(float(v))) for v in pixel]
    h, w = depth.shape
    if not (0 <= x < w and 0 <= y < h):
        return dict(accepted=False, world_xyz=None, loss_reason='outside_source_view')
    z = float(depth[y, x])
    if not np.isfinite(z) or not .001 < z < 10:
        return dict(accepted=False, world_xyz=None, loss_reason='invalid_public_depth')
    return dict(accepted=True, world_xyz=unproject(pixel, z, calibration).tolist(),
                loss_reason=None)


class Measurement:
    def __init__(self, parameters, initial_world, initial_seconds):
        self.parameters = parameters
        self.last_world = np.asarray(initial_world)
        self.last_seconds = initial_seconds

    def update(self, pixel, visible, depth, calibration, other_depth, other_calibration, seconds):
        p = self.parameters
        original = nearest(pixel, depth, calibration, visible)
        local = dict(original, cross_camera_status='not_checked', support_count=None,
                     patch_range_m=None, median_depth_m=None)
        primary = dict(local)
        if not original['accepted']:
            return original, local, primary
        x, y = [int(round(float(v))) for v in pixel]
        patch = depth[max(0, y-1):y+2, max(0, x-1):x+2]
        values = patch[np.isfinite(patch) & (patch > .001) & (patch < 10)]
        median = float(np.median(values)) if len(values) else None
        support = int(np.sum(np.abs(values - median) <= p['median_support_tolerance_m'])) if median is not None else 0
        spread = float(np.ptp(values)) if len(values) else None
        local.update(support_count=support, patch_range_m=spread, median_depth_m=median)
        reason = ('incomplete_source_patch' if patch.shape != (3, 3) else
                  'insufficient_surface_support' if support < p['minimum_support'] else
                  'source_depth_discontinuity' if spread > p['maximum_patch_range_m'] else None)
        if reason:
            local.update(accepted=False, world_xyz=None, loss_reason=reason)
            return original, local, dict(local)
        candidate = unproject(pixel, median, calibration)
        local.update(world_xyz=candidate.tolist())
        primary = dict(local)
        delta = float(np.linalg.norm(candidate - self.last_world))
        elapsed = seconds - self.last_seconds
        assert elapsed > 0
        bound = p['maximum_world_speed_m_s'] * elapsed + p['world_motion_slack_m']
        primary.update(world_change_m=delta, world_change_bound_m=bound,
                       elapsed_since_accepted_seconds=elapsed)
        if delta > bound:
            primary.update(accepted=False, world_xyz=None, loss_reason='implausible_world_change')
            return original, local, primary
        optical = (np.linalg.inv(np.asarray(other_calibration['camera_to_world'])) @ np.r_[candidate, 1.])[:3]
        h, w = other_depth.shape
        if optical[2] <= 0:
            status = 'outside_other_view'
        else:
            projected = np.asarray(other_calibration['intrinsic']) @ optical
            uv = projected[:2] / projected[2]
            ox, oy = [int(round(float(v))) for v in uv]
            primary['other_camera_pixel'] = uv.tolist()
            if not (0 <= ox < w and 0 <= oy < h):
                status = 'outside_other_view'
            else:
                z = float(other_depth[oy, ox])
                primary.update(other_camera_depth_m=z if np.isfinite(z) else None,
                               candidate_other_camera_depth_m=float(optical[2]))
                if not np.isfinite(z) or not .001 < z < 10:
                    status = 'invalid_other_depth'
                elif abs(z - optical[2]) <= p['cross_camera_depth_tolerance_m']:
                    status = 'corroborated'
                elif z < optical[2]:
                    status = 'other_view_occluded'
                else:
                    status = 'inconsistent_other_view'
                    primary.update(accepted=False, world_xyz=None,
                                   loss_reason='inconsistent_other_view')
        primary['cross_camera_status'] = status
        if primary['accepted']:
            self.last_world = candidate.copy()
            self.last_seconds = seconds
        return original, local, primary
