"""Generic robot-measurement criteria, with no task or object information."""
import numpy as np
from scipy.spatial.transform import Rotation


ARRIVAL = dict(position_tolerance_m=0.003, orientation_tolerance_rad=0.03,
               linear_speed_limit_m_s=0.005, angular_speed_limit_rad_s=0.05,
               finger_speed_limit_m_s=0.001, consecutive_samples=3,
               minimum_steps=10)


def pose_measurement(goal, qgoal, before, after, control_freq=20):
    r = Rotation.from_quat(after['robot0_eef_quat'])
    previous_r = Rotation.from_quat(before['robot0_eef_quat'])
    result = dict(
        position_error_m=float(np.linalg.norm(goal-after['robot0_eef_pos'])),
        orientation_error_rad=float((qgoal*r.inv()).magnitude()),
        linear_speed_m_s=float(np.linalg.norm(
            np.asarray(after['robot0_eef_pos'])-before['robot0_eef_pos'])*control_freq),
        angular_speed_rad_s=float((r*previous_r.inv()).magnitude()*control_freq),
        finger_speed_m_s=float(np.linalg.norm(after['robot0_gripper_qvel'])))
    result['settled_sample'] = bool(
        result['position_error_m'] <= ARRIVAL['position_tolerance_m'] and
        result['orientation_error_rad'] <= ARRIVAL['orientation_tolerance_rad'] and
        result['linear_speed_m_s'] <= ARRIVAL['linear_speed_limit_m_s'] and
        result['angular_speed_rad_s'] <= ARRIVAL['angular_speed_limit_rad_s'] and
        result['finger_speed_m_s'] <= ARRIVAL['finger_speed_limit_m_s'])
    return result
