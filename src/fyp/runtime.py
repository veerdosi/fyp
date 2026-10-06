"""Local setup and the sensor boundary. No task policy lives here."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBERO = ROOT / 'vendor/LIBERO'
CONFIG = ROOT / '.libero'
os.environ['LIBERO_CONFIG_PATH'] = str(CONFIG)
sys.path.insert(0, str(LIBERO))

TASK = 'KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it'
CAMERAS = ['agentview', 'robot0_eye_in_hand']
PROPRIO = ['robot0_eef_pos', 'robot0_eef_quat', 'robot0_joint_pos',
           'robot0_joint_vel', 'robot0_gripper_qpos', 'robot0_gripper_qvel',
           'robot0_eef_force', 'robot0_eef_torque']


def initialize_config():
    import yaml
    base = LIBERO / 'libero/libero'
    CONFIG.mkdir(exist_ok=True)
    (ROOT / 'vendor/datasets').mkdir(exist_ok=True)
    paths = dict(benchmark_root=str(base), bddl_files=str(base / 'bddl_files'),
                 init_states=str(base / 'init_files'), assets=str(base / 'assets'),
                 datasets=str(ROOT / 'vendor/datasets'))
    (CONFIG / 'config.yaml').write_text(yaml.safe_dump(paths))


def make_env(task=TASK, suite='libero_10', state_index=0, seed=0, size=256):
    initialize_config()
    import numpy as np
    import torch
    from libero.libero.envs import OffScreenRenderEnv
    base = LIBERO / 'libero/libero'
    bddl = base / 'bddl_files' / suite / (task + '.bddl')
    initial = torch.load(base / 'init_files' / suite / (task + '.pruned_init'),
                         map_location='cpu', weights_only=False)
    env = OffScreenRenderEnv(bddl_file_name=str(bddl), camera_names=CAMERAS,
                            camera_heights=size, camera_widths=size, camera_depths=True,
                            control_freq=20, horizon=10000, ignore_done=True)
    env.seed(seed)
    env.reset()
    state = np.asarray(initial[state_index]).copy()
    obs = add_robot_sensors(env, env.set_init_state(state))
    return env, obs, state


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
