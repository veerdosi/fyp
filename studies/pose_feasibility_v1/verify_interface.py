"""Paired fixed robot executions verify query integrity, boundaries and accounting."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from fyp.pose_preview import PosePreviewEpisode


def main():
    calibration=json.loads((ROOT/'studies/tool_hang_v2/protocol.json').read_text())['calibration']
    params=json.loads((HERE/'solver_parameters.json').read_text())
    verification=[]
    recordings=[]
    for enabled in [False,True]:
        folder=HERE/('fixed_preview' if enabled else 'fixed_waypoints')
        episode=PosePreviewEpisode(folder,task='ToolHang',suite='robosuite',seed=601,state_index=31,
            condition='fixed_sequence',size=256,max_steps=100,max_calls=10,settle_steps=20,
            calibration=calibration,interrupt_empty=True,preview_enabled=enabled,solver_parameters=params)
        pose=episode.obs['robot0_eef_pos'].copy()
        q=episode.obs['robot0_eef_quat'].copy()
        robot=episode.env.robots[0]
        current=episode.obs['robot0_joint_pos'].copy()
        assert np.array_equal(current,robot._joint_positions)
        pos,rot=episode.preview.pose(current)
        assert np.max(np.abs(pos-episode.env.sim.data.site_xpos[robot.eef_site_id]))<1e-12
        assert (rot*Rotation.from_matrix(episode.env.sim.data.get_body_xmat(robot.robot_model.eef_name)).inv()).magnitude()<1e-12
        assert np.array_equal(episode.preview.limits,episode.env.sim.model.jnt_range[robot._ref_joint_indexes])
        # Same public-input calculation exists in both conditions.
        direct=episode.preview.solve(current,pose,q)
        assert direct['best']['solution_found']
        query_count=0
        if enabled:
            before=episode.env.get_sim_state().copy()
            valid=episode.command(dict(command=dict(type='preview',poses=[dict(position=pose.tolist(),quaternion_xyzw=q.tolist())],reason='Fixed public-robot calculation verification.')))
            assert np.array_equal(before,episode.env.get_sim_state()) and episode.steps==20
            assert valid['poses'][0]['best']==direct['best']
            invalid=episode.command(dict(command=dict(type='preview',poses=[dict(position=[0,0,2])],reason='Fixed workspace validation verification.')))
            assert 'validation_error' in invalid and episode.calls==2 and episode.steps==20
            assert np.array_equal(before,episode.env.get_sim_state())
            query_count=2
        target=pose+np.array([0,0,.01])
        result=episode.command(dict(command=dict(type='move',waypoints=[dict(position=target.tolist(),quaternion_xyzw=q.tolist(),gripper=-1,steps=30)],reason='Identical fixed motion after optional query.')))
        assert 'validation_error' not in result
        episode.finish('fixed_preview_verification');episode.events.close()
        recorded=np.load(folder/'trajectory.npz');recordings.append(recorded)
        verification.append(dict(folder=str(folder),preview_enabled=enabled,query_decisions=query_count,
            model_decisions=episode.calls,control_steps=episode.steps,raw_encoder_exact=True,
            known_model_fk_and_joint_bounds_exact=True,public_calculation_matches_query=True,
            query_does_not_advance_physics=True,invalid_query_consumes_decision=True,actual_astra_requests=0))
    assert np.array_equal(recordings[0]['initial'],recordings[1]['initial'])
    assert np.array_equal(recordings[0]['actions'],recordings[1]['actions'])
    assert np.array_equal(recordings[0]['states'],recordings[1]['states'])
    # Consequential budget boundary: a rejected final query must terminate too.
    episode=PosePreviewEpisode(HERE/'fixed_query_budget',task='ToolHang',suite='robosuite',seed=601,state_index=31,
        condition='fixed_sequence',size=256,max_steps=100,max_calls=1,settle_steps=20,
        calibration=calibration,interrupt_empty=True,preview_enabled=True,solver_parameters=params)
    rejected=episode.command(dict(command=dict(type='preview',poses=[],reason='Fixed decision-budget boundary.')))
    assert rejected['episode_stopped']=='budget_exhausted' and episode.closed and episode.calls==1 and episode.steps==20
    episode.events.close()
    source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/'src/fyp/pose_preview.py',ROOT/'src/fyp/kinematic_preview.py',Path(__file__),HERE/'solver_parameters.json']}
    result=dict(all_pass=True,paired_initial_actions_states_exact=True,query_budget_boundary_pass=True,
        fixtures=verification,source_hashes=source_hashes,actual_astra_requests=0,
        reproduce='.venv/bin/python studies/pose_feasibility_v1/verify_interface.py (fresh fixture folders required)')
    (HERE/'verification_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
