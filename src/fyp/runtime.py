"""Local setup and the sensor boundary. No task policy lives here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = 'ToolHang'
CAMERAS = ['agentview', 'robot0_eye_in_hand']
PROPRIO = ['robot0_eef_pos', 'robot0_eef_quat', 'robot0_joint_pos',
           'robot0_joint_vel', 'robot0_gripper_qpos', 'robot0_gripper_qvel',
           'robot0_eef_force', 'robot0_eef_torque']


def make_env(task=TASK, suite='robosuite', state_index=0, seed=0, size=256):
    if suite != 'robosuite':
        raise ValueError('Only native robosuite tasks are active. Historical LIBERO replay requires the original archived revision and dependencies.')
    from .robosuite_runtime import make_native_env
    return make_native_env(task, state_index, seed, size, CAMERAS)


def add_robot_sensors(env, obs):
    obs['robot0_eef_force'] = env.robots[0].ee_force.copy()
    obs['robot0_eef_torque'] = env.robots[0].ee_torque.copy()
    return obs


def proprio(obs):
    return {key: obs[key].tolist() for key in PROPRIO if key in obs}


def sensor_images(env, obs):
    from robosuite.utils.camera_utils import get_real_depth_map
    return {name: (obs[name + '_image'][::-1].copy(),
                   get_real_depth_map(env.sim, obs[name + '_depth'])[::-1, :, 0].copy())
            for name in CAMERAS}
