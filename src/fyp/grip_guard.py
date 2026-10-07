"""Timed waypoints with identical sensing and optional empty-closure handoff."""
import numpy as np
from scipy.spatial.transform import Rotation
from .episode import Episode
from .runtime import proprio
from .motion import pose_measurement
from .sensor_monitor import SensorMonitor


class GripFeedbackEpisode(Episode):
    def __init__(self,*args,calibration,interrupt_empty=False,**kwargs):
        self.interrupt_empty=interrupt_empty
        self.feedback=SensorMonitor(calibration['weights'],calibration['empty_max'])
        self.feedback_rows=[]
        self.robot_history=[]
        super().__init__(*args,**kwargs)
        self.config['sensor_feedback']=dict(calibration=calibration,interrupt_empty=interrupt_empty,
            semantics='Only an explicitly armed empty-sized closure can cancel execution; flags do not certify acquisition.')
        from .episode import write_json
        write_json(self.folder/'config.json',self.config)

    def step(self,*args,**kwargs):
        super().step(*args,**kwargs)
        self.robot_history.append(proprio(self.obs))
        self.robot_history=self.robot_history[-3:]

    def validate_move(self,command):
        points=super().validate_move(command)
        for wp in points:
            flag=wp.get('abort_if_empty_close',False)
            if type(flag) is not bool:
                raise ValueError('abort_if_empty_close must be boolean')
            if flag and (wp['gripper']!=1 or wp['steps']<10):
                raise ValueError('armed empty-closure monitoring requires gripper +1 and at least ten steps')
        return points

    def move(self,points):
        outmax=np.asarray(self.env.robots[0].controller.output_max)
        report=dict(condition=self.config['condition'],interrupt_empty=self.interrupt_empty,waypoints=[],
            note='Sensor flags are observations; not-empty-sized is not acquired, seated or complete.')
        for index,wp in enumerate(points):
            goal=np.asarray(wp['position']);qgoal=Rotation.from_quat(wp.get('quaternion_xyzw',self.obs['robot0_eef_quat']))
            resolved=dict(wp,quaternion_xyzw=qgoal.as_quat().tolist())
            self.feedback.begin(resolved,self.robot_history or [proprio(self.obs)])
            first=self.steps+1;flags=[];stop=False
            for iteration in range(wp['steps']):
                before=proprio(self.obs);p=self.obs['robot0_eef_pos'];r=Rotation.from_quat(self.obs['robot0_eef_quat'])
                dp=goal-p;norm=np.linalg.norm(dp)
                if norm>.015:dp*=.015/norm
                dr=(qgoal*r.inv()).as_rotvec();angle=np.linalg.norm(dr)
                if angle>.15:dr*=.15/angle
                action=np.r_[np.clip(np.r_[dp,dr]/outmax,-1,1),wp['gripper']]
                self.step(action,self.calls,waypoint_index=index)
                after=proprio(self.obs);measured=self.feedback.update(before,after)
                row=dict(step=self.steps,command_id=self.calls,waypoint_index=index,
                    armed=wp.get('abort_if_empty_close',False),**measured)
                self.feedback_rows.append(row);flags.append(row)
                with (self.folder/'sensor_feedback.jsonl').open('a') as handle:
                    import json
                    handle.write(json.dumps(row)+'\n')
                if self.interrupt_empty and row['armed'] and measured['flags']['empty_sized_closure']:
                    stop=True;break
            report['waypoints'].append(dict(waypoint_index=index,first_step=first,last_step=self.steps,
                requested_steps=wp['steps'],executed_steps=self.steps-first+1,armed=wp.get('abort_if_empty_close',False),
                first_flags={kind:next((row['step'] for row in flags if row['flags'][kind]),None) for kind in self.feedback.counts},
                terminal_measurement=pose_measurement(goal,qgoal,before,after),
                status='empty_sized_closure' if stop else 'duration_elapsed',
                resolved_quaternion_xyzw=qgoal.as_quat().tolist()))
            if stop:
                report.update(stop_reason='armed_empty_sized_closure',remaining_waypoints_cancelled=len(points)-index-1,
                    handoff='Fresh observation; policy selects any recovery.')
                return report
        report.update(stop_reason='sequence_complete',remaining_waypoints_cancelled=0)
        return report
