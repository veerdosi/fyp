"""Screen known-robot pose preview against the fixed development waypoints."""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.runtime import make_env
from kinematic_preview import Preview


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = 1
    while (HERE/f'feasibility_attempt_{index:03d}').exists():
        index += 1
    folder = HERE/f'feasibility_attempt_{index:03d}'
    folder.mkdir()
    path = folder/'result.json'
    protocol = json.loads((HERE/'feasibility_screen_protocol.json').read_text())
    prior = json.loads((HERE/'discriminator_result.json').read_text())
    preview = Preview((HERE/'robot_kinematics.xml').read_text(),protocol)
    frozen = dict(protocol_sha256=sha(HERE/'feasibility_screen_protocol.json'),
        code_and_model_hashes={n:sha(HERE/n) for n in ['feasibility_screen.py','kinematic_preview.py','robot_kinematics.xml']})
    (folder/'configuration.json').write_text(json.dumps(frozen,indent=2)+'\n')
    began = time.monotonic()
    rows = []
    for name in dict.fromkeys(s['episode'] for s in prior['samples']):
        run = ROOT/'runs'/name
        config = json.loads((run/'config.json').read_text())
        saved = np.load(run/'trajectory.npz')
        assert sha(run/'trajectory.npz') == prior['source_hashes'][str((run/'trajectory.npz').relative_to(ROOT))]
        env,_,_=make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
        robot,sim=env.robots[0],env.sim
        original_limits = sim.model.jnt_range[robot._ref_joint_indexes]
        assert np.array_equal(preview.limits,original_limits), 'Robot joint bounds differ'
        for sample in [s for s in prior['samples'] if s['episode']==name]:
            for w in sample['waypoints']:
                sim.set_state_from_flattened(saved['states'][w['first_step']-2])
                sim.forward()
                current = sim.data.qpos[robot._ref_joint_pos_indexes].copy()
                position, rotation = preview.pose(current)
                ep = sim.data.site_xpos[robot.eef_site_id]
                er = Rotation.from_matrix(sim.data.get_body_xmat(robot.robot_model.eef_name))
                pe = float(np.max(np.abs(position-ep)))
                re = float((rotation*er.inv()).magnitude())
                assert pe < 1e-12 and re < 1e-12, 'Robot-only FK boundary differs'
                tick = time.monotonic()
                result = preview.solve(current,w['target_position'],w['resolved_target_quaternion'])
                rows.append(dict(episode=name,decision=sample['decision'],waypoint=w['index'],
                    label=sample['label'],current_q_rad=current.tolist(),
                    target_position=w['target_position'],target_quaternion=w['resolved_target_quaternion'],
                    fk_position_max_error_m=pe,fk_rotation_error_rad=re,seconds=time.monotonic()-tick,
                    recorded_terminal_measurement=w['terminal_measurement'],**result))
                print(name,sample['decision'],w['index'],result['best']['solution_found'],
                      round(result['best']['position_error_m'],5),round(result['best']['orientation_error_rad'],5),flush=True)
        env.close()
    result = dict(protocol_sha256=sha(HERE/'feasibility_screen_protocol.json'),
        discriminator_result_sha256=sha(HERE/'discriminator_result.json'),
        source_hashes={p:sha(HERE/p) for p in ['feasibility_screen.py','kinematic_preview.py','robot_kinematics.xml']},
        actual_astra_requests=0,total_seconds=time.monotonic()-began,samples=rows,
        scope='Retrospective robot-only IK; private states supply robot joint inputs for development only.',
        public_boundary_gap='Existing native policy observations omit joint positions. New policy comparisons must expose actual joint encoder positions and the known robot model equally.',
        reproduce='.venv/bin/python studies/mechanism_selection/feasibility_screen.py (preserve prior result first)')
    path.write_text(json.dumps(result,indent=2)+'\n')
    (HERE/'feasibility_latest.json').write_text(json.dumps(dict(attempt=folder.name,
        completed=True,result=str(path)),indent=2)+'\n')


if __name__=='__main__':
    main()
