"""Bounded pose IK on a supplied robot-only model; no scene or scoring access."""
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


class Preview:
    def __init__(self, xml, parameters):
        self.model = mujoco.MjModel.from_xml_string(xml)
        self.data = mujoco.MjData(self.model)
        self.parameters = parameters
        m = self.model
        names = [f'robot0_joint{i}' for i in range(1,8)]
        ids = [mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in names]
        self.qids = m.jnt_qposadr[ids]
        self.limits = m.jnt_range[ids]
        self.site = mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_SITE,'gripper0_grip_site')
        self.body = mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'robot0_right_hand')
        assert min(ids+[self.site,self.body]) >= 0

    def pose(self, q):
        self.data.qpos[self.qids] = q
        mujoco.mj_forward(self.model,self.data)
        return self.data.site_xpos[self.site].copy(), Rotation.from_matrix(
            self.data.xmat[self.body].reshape(3,3).copy())

    def solve(self, current_q, goal_position, goal_quaternion):
        p = self.parameters
        current_q = np.asarray(current_q)
        goal_position = np.asarray(goal_position)
        goal_rotation = Rotation.from_quat(goal_quaternion)
        lower = self.limits[:,0]+p['joint_bound_margin_rad']
        upper = self.limits[:,1]-p['joint_bound_margin_rad']
        offset = np.asarray(p['fixed_offset_rad'])
        seeds = [current_q, np.asarray(p['nominal_q_rad']),current_q+offset,current_q-offset]
        results = []
        def residual(q):
            position, rotation = self.pose(q)
            return np.r_[position-goal_position,p['orientation_residual_scale_m_per_rad'] *
                (goal_rotation*rotation.inv()).as_rotvec()]
        for name, seed in zip(p['seeds'],seeds):
            fit = least_squares(residual,np.clip(seed,lower+1e-8,upper-1e-8),
                bounds=(lower,upper),max_nfev=p['maximum_function_evaluations_per_seed'],
                ftol=1e-9,xtol=1e-9,gtol=1e-9)
            position, rotation = self.pose(fit.x)
            pe = float(np.linalg.norm(position-goal_position))
            re = float((goal_rotation*rotation.inv()).magnitude())
            results.append(dict(seed=name,q_rad=fit.x.tolist(),position_error_m=pe,
                orientation_error_rad=re,solution_found=pe<=p['position_tolerance_m'] and
                   re<=p['orientation_tolerance_rad'],nfev=fit.nfev,
                minimum_joint_margin_rad=float(np.min(np.minimum(fit.x-self.limits[:,0],
                                                     self.limits[:,1]-fit.x))),
                weighted_residual_norm=float(np.linalg.norm(residual(fit.x)))))
        best = min(results,key=lambda r:(not r['solution_found'],r['weighted_residual_norm']))
        return dict(best=best,seeds=results,note='Pose IK only; no dynamic/contact or task certificate.')
