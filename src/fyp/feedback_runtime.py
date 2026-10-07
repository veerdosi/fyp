"""Publish the same processed robot feedback in both experiment conditions."""
import json,time
import numpy as np
from .grip_guard import GripFeedbackEpisode
from .sensor_monitor import compensate,opening,PARAMETERS
from .runtime import proprio
from .episode import write_json


class SharedFeedbackEpisode(GripFeedbackEpisode):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.publish_feedback()

    def publish_feedback(self):
        began=time.monotonic();p=proprio(self.obs)
        folder=self.public/f"obs_{self.latest['observation_id']:04d}"
        calibration=dict(weights=self.feedback.weights.tolist(),empty_max=self.feedback.empty_max,
            empty_threshold_m=self.feedback.empty_max+.002,parameters=PARAMETERS,
            feature_definition='[1, R(public quaternion)^T*(0,0,-9.81), sum(abs(finger qpos))]',
            note='Empty-gripper gravity reference; dynamics and held-object weight remain. Not an acquisition/seating/contact certificate.')
        write_json(self.public/'feedback_calibration.json',calibration)
        rows=[r for r in self.feedback_rows if r['command_id']==self.calls]
        summary=[]
        for index in sorted({r['waypoint_index'] for r in rows}):
            group=[r for r in rows if r['waypoint_index']==index]
            summary.append(dict(waypoint_index=index,first_step=group[0]['step'],last_step=group[-1]['step'],
                armed=group[0]['armed'],first_flags={kind:next((r['step'] for r in group if r['flags'][kind]),None) for kind in self.feedback.counts},
                terminal_sensor_measurement=group[-1]))
        with (folder/'sensor_feedback_samples.jsonl').open('w') as handle:
            for row in rows:
                handle.write(json.dumps(row)+'\n')
        value=dict(observation_id=self.latest['observation_id'],step=self.steps,
            opening_m=opening(p),finger_speed_m_s=float(np.linalg.norm(p['robot0_gripper_qvel'])),
            current_compensated_wrench=compensate(p,self.feedback.weights).tolist(),
            calibration_file=str(self.public/'feedback_calibration.json'),last_motion_summary=summary,
            samples_file=str(folder/'sensor_feedback_samples.jsonl'),
            note='The same processed sensing is available in both conditions. Flags are observations, not task outcomes.')
        write_json(folder/'sensor_feedback.json',value)
        self.latest['feedback_file']=str(folder/'sensor_feedback.json')
        write_json(folder/'observation.json',self.latest);write_json(self.public/'latest.json',self.latest)
        with (self.folder/'feedback_publication.jsonl').open('a') as handle:
            handle.write(json.dumps(dict(observation_id=self.latest['observation_id'],seconds=time.monotonic()-began))+'\n')

    def command(self,body):
        result=super().command(body)
        if 'folder' in result:
            self.publish_feedback()
            result['feedback_file']=self.latest['feedback_file']
        return result
