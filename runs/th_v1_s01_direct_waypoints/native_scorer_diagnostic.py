"""Offline scoring diagnosis from the saved final state; never a policy input."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

run = Path(__file__).resolve().parent
root = run.parents[1]
sys.path.insert(0, str(root / 'src'))
from fyp.runtime import make_env
from robosuite.utils.sim_utils import check_contact

config = json.loads((run / 'config.json').read_text())
env, _, _ = make_env(task=config['task'], suite=config['suite'],
                     state_index=config['state_index'], seed=config['seed'], size=config['size'])
trajectory = np.load(run / 'trajectory.npz')
env.set_init_state(trajectory['states'][-1])
native = env.env
sim = native.sim
endpoint = sim.data.site_xpos[native.obj_site_id['frame_hang_site']].copy()
vector = sim.data.site_xpos[native.obj_site_id['frame_intersection_site']] - endpoint
length = np.linalg.norm(vector)
axis = vector / length
robot_contact = any(check_contact(sim, group, native.tool.contact_geoms)
                    for group in [native.robots[0].gripper.important_geoms['left_fingerpad'],
                                  native.robots[0].gripper.important_geoms['right_fingerpad']])
holes = {}
for hole in (1, 2):
    names = [f'tool_hole{hole}_hc_{i}' for i in range(native.tool_args['ngeoms'])]
    center = sim.data.site_xpos[sim.model.site_name2id(f'tool_hole{hole}_center')].copy()
    displacement = center - endpoint
    dot = np.dot(displacement, axis)
    distance = np.linalg.norm(displacement - dot * axis)
    opposed = [sim.data.geom_xpos[sim.model.geom_name2id(names[i])]
               for i in (0, native.tool_args['ngeoms'] // 2)]
    straddle_dot = np.dot(np.cross(opposed[0] - endpoint, axis),
                          np.cross(opposed[1] - endpoint, axis))
    threshold = native.tool_args[f'inner_radius_{hole}'] - native.frame_args['frame_thickness'] / 2
    fraction = dot / length
    checks = dict(robot_released=not robot_contact,
                  hole_contacts_horizontal_hook=bool(check_contact(sim, names, 'frame_horizontal_frame')),
                  center_close_to_hook_line=bool(distance < threshold),
                  opposed_geoms_straddle_hook_line=bool(straddle_dot < 0),
                  insertion_fraction_between_005_and_1=bool(0.05 < fraction < 1.0))
    holes[str(hole)] = dict(center_xyz=center.tolist(), distance_to_hook_line_m=float(distance),
                            distance_threshold_m=float(threshold), straddle_dot=float(straddle_dot),
                            insertion_fraction=float(fraction), checks=checks,
                            all_checks=all(checks.values()))
source = Path(sys.modules[native.__class__.__module__].__file__)
result = dict(scope='Private offline diagnosis; hole 1 is the native scored larger hole. Hole 2 is diagnostic only.',
              final_control_step=config.get('control_steps', len(trajectory['actions'])),
              native_success=bool(env.check_success()),
              native_goals=env.diagnostic_goals(), hook_endpoint_xyz=endpoint.tolist(),
              hook_axis=axis.tolist(), hook_length_m=float(length), holes=holes,
              scorer_source=str(source), scorer_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              reproduce='.venv/bin/python runs/th_v1_s01_direct_waypoints/native_scorer_diagnostic.py')
(run / 'native_scorer_diagnostic.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
env.close()
