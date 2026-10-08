"""Optional robot-only pose calculation; robot motion remains model-selected."""
import hashlib
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import numpy as np
from .feedback_runtime import SharedFeedbackEpisode
from .kinematic_preview import Preview
from .episode import write_json


def known_robot_xml(robot):
    tree = ET.fromstring(robot.robot_model.get_xml())
    # Known mechanical chain and base calibration only. No task objects or assets.
    for parent in list(tree.iter()):
        for node in list(parent):
            if node.tag in {'geom','asset','actuator','sensor','camera','contact','equality'}:
                parent.remove(node)
    compiler = tree.find('compiler')
    if compiler is None:
        compiler = ET.SubElement(tree,'compiler')
    compiler.set('angle','radian')
    return ET.tostring(tree,encoding='unicode')


class PosePreviewEpisode(SharedFeedbackEpisode):
    def __init__(self,*args,preview_enabled,solver_parameters,**kwargs):
        self.preview_enabled = preview_enabled
        self.solver_parameters = solver_parameters
        super().__init__(*args,**kwargs)
        folder = self.public/'robot_kinematics'
        folder.mkdir()
        xml = known_robot_xml(self.env.robots[0])
        (folder/'robot.xml').write_text(xml)
        write_json(folder/'parameters.json',solver_parameters)
        shutil.copyfile(Path(__file__).with_name('kinematic_preview.py'),folder/'kinematic_preview.py')
        self.preview = Preview(xml,solver_parameters)
        original_limits = self.env.sim.model.jnt_range[self.env.robots[0]._ref_joint_indexes]
        assert np.array_equal(self.preview.limits,original_limits)
        self.config['pose_preview'] = dict(enabled=preview_enabled,
            parameters=solver_parameters,public_model_folder=str(folder),
            model_sha256=hashlib.sha256(xml.encode()).hexdigest(),
            known_robot_joint_bounds_exact=True,
            semantics='Optional robot-only query; never chooses, cancels or executes motion.')
        write_json(self.folder/'config.json',self.config)

    def snapshot(self):
        self.obs['robot0_joint_pos'] = self.env.robots[0]._joint_positions.copy()
        return super().snapshot()

    def query(self,candidates):
        if not self.preview_enabled:
            raise ValueError('preview query unavailable in this condition; public calculations remain allowed')
        if not isinstance(candidates,list) or not 1<=len(candidates)<=4:
            raise ValueError('poses must contain 1..4 candidate targets')
        resolved = []
        for candidate in candidates:
            pos = np.asarray(candidate.get('position'),dtype=float)
            quat = np.asarray(candidate.get('quaternion_xyzw',self.obs['robot0_eef_quat']),dtype=float)
            if pos.shape!=(3,) or not np.all(np.isfinite(pos)):
                raise ValueError('position must be three finite metres')
            if np.any(pos<[-.55,-.55,.76]) or np.any(pos>[.55,.65,1.6]):
                raise ValueError('candidate outside workspace')
            if quat.shape!=(4,) or not np.all(np.isfinite(quat)) or abs(np.linalg.norm(quat)-1)>.01:
                raise ValueError('quaternion_xyzw must be unit length')
            resolved.append((pos,quat))
        q = self.env.robots[0]._joint_positions.copy()  # Same genuine encoder input published to both conditions.
        results = []
        for pos,quat in resolved:
            tick = time.monotonic()
            calculated = self.preview.solve(q,pos,quat)
            results.append(dict(position=pos.tolist(),quaternion_xyzw=quat.tolist(),
                seconds=time.monotonic()-tick,**calculated))
        result = dict(observation_id=self.latest['observation_id'],step=self.steps,
            model_calls=self.calls,remaining_model_calls=self.max_calls-self.calls,
            remaining_steps=self.max_steps-self.steps,robot0_joint_pos=q.tolist(),poses=results,
            note='No motion occurred. No solution means this bounded search found none; it does not prove global unreachability. Solutions do not certify dynamic arrival, collision clearance, grasp or task success.')
        path = Path(self.latest['folder'])/f'preview_{self.calls:03d}.json'
        write_json(path,result)
        result['preview_file']=str(path)
        return result

    def command(self,body):
        if body.get('command',{}).get('type')!='preview':
            return super().command(body)
        began = time.monotonic()
        if self.closed or self.calls>=self.max_calls:
            raise ValueError('episode closed or decision budget exhausted')
        policy = body.get('policy')
        if policy and (policy.get('model')!='gpt-6-astra' or policy.get('reasoning_effort')!='medium'):
            raise ValueError('robot policy must be gpt-6-astra at medium effort')
        self.calls += 1
        write_json(self.folder/f'policy_turn_{self.calls:03d}.json',body)
        event = dict(call=self.calls,input_observation_id=self.latest['observation_id'],
            command=body['command'],wall_seconds=time.monotonic()-self.t0)
        before = self.env.get_sim_state().copy()  # Integrity assertion only; not solver input.
        try:
            result = self.query(body['command'].get('poses'))
        except (ValueError,KeyError,TypeError) as exc:
            result = dict(validation_error=str(exc),observation=self.latest,model_calls=self.calls,
                remaining_model_calls=self.max_calls-self.calls,remaining_steps=self.max_steps-self.steps)
        assert np.array_equal(before,self.env.get_sim_state()),'Query changed live physics'
        if self.calls>=self.max_calls:
            self.finish('model_call_budget')
            result['episode_stopped']='budget_exhausted'
        event.update(result=result,execution_wall_seconds=time.monotonic()-began,
                     completed_wall_seconds=time.monotonic()-self.t0)
        self.events.write(json.dumps(event,allow_nan=False)+'\n')
        self.events.flush()
        return result
