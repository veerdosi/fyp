"""Private scoring geometry; never supplied to OnlinePointMeasurement."""
import mujoco
import numpy as np
from point_measurement import world_point


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
                body_name=sim.model.body_id2name(body), initial_ray_depth_residual_m=residual,
                initial_image_world=point)


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
                image_time_error_p95_m=float(np.percentile([r['image_time_error_m'] for r in accepted],95)) if accepted else None,
                camera_age_max_seconds=max((r['camera_age_seconds'] for r in rows),default=None),
                occluded_false_valid_rate=false_valid,
                gate_pass=coverage is not None and coverage >= .8 and p95 is not None and p95 <= .003
                          and false_valid is not None and false_valid <= .05)


