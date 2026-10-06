"""Native MuJoCo task adapter; no robot policy or task-specific execution."""
import numpy as np

TASK_INSTRUCTIONS = {
    'NutAssemblySquare': 'Pick up the square nut and fit it fully onto the square peg, then release it and withdraw the gripper.',
    'NutAssemblyRound': 'Pick up the round nut and fit it fully onto the round peg, then release it and withdraw the gripper.',
    'ToolHang': 'Assemble the hook frame into the stand, then hang the tool by its hole on the hook and release it.',
}


class SensorEnv:
    def __init__(self, env):
        self.env = env

    def __getattr__(self, name):
        return getattr(self.env, name)

    def get_sim_state(self):
        return self.env.sim.get_state().flatten()

    def set_init_state(self, state):
        self.env.sim.set_state_from_flattened(state)
        self.env.sim.forward()
        self.env._update_observables(force=True)
        return self.env._get_observations(force_update=True)

    def check_success(self):
        return self.env._check_success()

    def diagnostic_goals(self):
        # Private scoring only; never passed into the executor or policy.
        if self.env.__class__.__name__ == 'ToolHang':
            return [{'predicate': ['frame_assembled'], 'satisfied': bool(self.env._check_frame_assembled())},
                    {'predicate': ['tool_on_frame'], 'satisfied': bool(self.env._check_tool_on_frame())}]
        return [{'predicate': ['native_task_success'], 'satisfied': bool(self.check_success())}]


def make_native_env(task, state_index, seed, size, cameras):
    if task not in TASK_INSTRUCTIONS:
        raise ValueError(f'Unsupported native screening task: {task}')
    import robosuite
    from .runtime import add_robot_sensors
    layout_seed = int(np.random.SeedSequence([seed, state_index]).generate_state(1)[0])
    np.random.seed(layout_seed)
    env = robosuite.make(
        task, robots='Panda',
        controller_configs=robosuite.load_controller_config(default_controller='OSC_POSE'),
        initialization_noise=None, has_renderer=False, has_offscreen_renderer=True,
        use_camera_obs=True, use_object_obs=True, camera_names=cameras,
        camera_heights=size, camera_widths=size, camera_depths=True,
        control_freq=20, horizon=10000, ignore_done=True, reward_shaping=False,
    )
    obs = env.reset()
    wrapped = SensorEnv(env)
    initial = wrapped.get_sim_state().copy()
    return wrapped, add_robot_sensors(wrapped, obs), initial
