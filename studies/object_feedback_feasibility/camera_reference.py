"""Private image-time geometric references. Never imported by the tracker."""
import numpy as np
from robosuite.utils.camera_utils import (get_real_depth_map,
    get_camera_intrinsic_matrix, get_camera_extrinsic_matrix)


class CameraReferenceCapture:
    def __init__(self, env, segments, reference_function, truth_function):
        self.env = env
        self.segments = segments
        self.reference_function = reference_function
        self.truth_function = truth_function
        self.step = 0
        self.references = {}
        self.measurements = {}
        self.seeds = {}
        for camera in ['agentview','robot0_eye_in_hand']:
            observable = env.env._observables[camera+'_image']
            original = observable._sensor

            def sensor(cache, camera=camera, original=original):
                rgb = original(cache)
                depth = get_real_depth_map(env.sim,cache[camera+'_depth'])[::-1,:,0]
                cal = dict(intrinsic=get_camera_intrinsic_matrix(env.sim,camera,*depth.shape).tolist(),
                           camera_to_world=get_camera_extrinsic_matrix(env.sim,camera).tolist())
                measured = {}
                for key, ref in self.references.get(camera,{}).items():
                    point, visible = self.truth_function(env.sim,ref,depth,cal)
                    measured[key] = dict(point=point,visible=visible)
                for segment in self.segments:
                    if segment['start_step'] != self.step:
                        continue
                    for p in segment['points']:
                        if p['camera'] != camera:
                            continue
                        key = (p['query_decision'],p['pixel_index'])
                        self.seeds[key] = self.reference_function(env.sim,[p['u'],p['v']],depth,cal)
                self.measurements[camera] = dict(time=float(env.sim.data.time),
                    calibration=cal,points=measured)
                return rgb

            # Do not call set_sensor: its validation invokes a fresh sensor.
            # This wrapper calls the original sensor exactly once and only reads
            # scene geometry at the instant its camera frame is sampled.
            sensor.__modality__ = original.__modality__
            observable._sensor = sensor

    def activate(self, camera, points, references):
        self.references[camera] = {(p['query_decision'],p['pixel_index']):ref
                                   for p,ref in zip(points,references)}

    def current_world(self, ref):
        if ref is None:
            return None
        sim = self.env.sim
        return sim.data.xmat[ref['body']].reshape(3,3) @ ref['local'] + sim.data.xpos[ref['body']]
