"""Sensor-only load/progress/empty-size signals; no simulator or task imports."""
from collections import deque
import numpy as np
from scipy.spatial.transform import Rotation

PARAMETERS=dict(force_change_N=5.,torque_change_Nm=.5,consecutive=3,minimum_steps=10,
    position_tolerance_m=.003,orientation_tolerance_rad=.03,progress_window_steps=10,
    minimum_position_progress_m=.001,minimum_orientation_progress_rad=.01,
    linear_speed_m_s_max=.005,angular_speed_rad_s_max=.05,finger_speed_m_s_max=.001,
    empty_opening_margin_m=.002)


def opening(p):
    return float(sum(abs(v) for v in p['robot0_gripper_qpos']))


def compensate(p,weights):
    features=np.r_[1.,Rotation.from_quat(p['robot0_eef_quat']).inv().apply([0,0,-9.81]),opening(p)]
    return np.r_[p['robot0_eef_force'],p['robot0_eef_torque']]-features@weights


class SensorMonitor:
    def __init__(self,weights,empty_max):
        self.weights=np.asarray(weights);self.empty_max=empty_max

    def begin(self,waypoint,prior):
        self.goal=np.asarray(waypoint['position']);self.qgoal=Rotation.from_quat(waypoint['quaternion_xyzw'])
        self.gripper=waypoint['gripper'];self.tare=np.mean([compensate(p,self.weights) for p in prior[-3:]],axis=0)
        self.history=deque(maxlen=11);self.n=0
        self.counts={k:0 for k in ['load_change','stalled_motion','empty_sized_closure']}
        p=prior[-1]
        self.history.append((float(np.linalg.norm(self.goal-p['robot0_eef_pos'])),float((self.qgoal*Rotation.from_quat(p['robot0_eef_quat']).inv()).magnitude())))
        self.quiet=deque(maxlen=3)

    def update(self,before,after):
        self.n+=1
        error=float(np.linalg.norm(self.goal-after['robot0_eef_pos']))
        angle=float((self.qgoal*Rotation.from_quat(after['robot0_eef_quat']).inv()).magnitude())
        self.history.append((error,angle))
        linear=float(np.linalg.norm(np.asarray(after['robot0_eef_pos'])-before['robot0_eef_pos'])*20)
        angular=float((Rotation.from_quat(after['robot0_eef_quat'])*Rotation.from_quat(before['robot0_eef_quat']).inv()).magnitude()*20)
        finger=float(np.linalg.norm(after['robot0_gripper_qvel']))
        self.quiet.append(linear<=.005 and angular<=.05)
        delta=compensate(after,self.weights)-self.tare
        force=float(np.linalg.norm(delta[:3]));torque=float(np.linalg.norm(delta[3:]))
        pos_progress=self.history[0][0]-error if len(self.history)==11 else None
        rot_progress=self.history[0][1]-angle if len(self.history)==11 else None
        unfinished=error>.003 or angle>.03
        no_progress=pos_progress is not None and (error<=.003 or pos_progress<.001) and (angle<=.03 or rot_progress<.01)
        raw=dict(load_change=force>=5 or torque>=.5,
            stalled_motion=bool(unfinished and no_progress and len(self.quiet)==3 and all(self.quiet)),
            empty_sized_closure=self.gripper==1 and opening(after)<=self.empty_max+.002 and finger<=.001)
        for key,value in raw.items():
            self.counts[key]=self.counts[key]+1 if value else 0
        flags={key:self.n>=10 and count>=3 for key,count in self.counts.items()}
        return dict(waypoint_step=self.n,position_error_m=error,orientation_error_rad=angle,
            linear_speed_m_s=linear,angular_speed_rad_s=angular,finger_speed_m_s=finger,opening_m=opening(after),
            force_change_N=force,torque_change_Nm=torque,position_progress_10_steps_m=pos_progress,
            orientation_progress_10_steps_rad=rot_progress,raw=raw,flags=flags)
