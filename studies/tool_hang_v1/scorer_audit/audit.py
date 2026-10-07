"""Offline native-scorer audit; never a policy or executor measurement source."""
import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env
from robosuite.utils.sim_utils import check_contact


def inspect(run, step=None):
    config = json.loads((run / 'config.json').read_text())
    trajectory = np.load(run / 'trajectory.npz')
    count = len(trajectory['actions'])
    step = count if step is None else step
    env, _, _ = make_env(**{k: config[k] for k in ['task', 'suite', 'seed', 'state_index', 'size']})
    env.set_init_state(trajectory['states'][step - 1])
    n, sim = env.env, env.env.sim
    site = lambda name: sim.data.site_xpos[n.obj_site_id[name]].copy()
    base = sim.data.geom_xpos[n.obj_geom_id['stand_base']].copy()
    stand = site('stand_mount_site') - base
    tilt = float(np.arccos(np.clip(stand[2] / np.linalg.norm(stand), -1, 1)))
    tip = site('frame_tip_site' if 'frame_tip_site' in n.obj_site_id else 'frame_mount_site')
    origin = site('frame_mount_site')
    rod = site('frame_intersection_site') - origin
    rod /= np.linalg.norm(rod)
    walls = [sim.data.geom_xpos[n.obj_geom_id[f'stand_wall_{i}']] - origin for i in range(4)]
    dots = [float(np.dot(np.cross(walls[i], rod), np.cross(walls[i+2], rod))) for i in range(2)]
    distance = float(np.linalg.norm(tip - base))
    frame_checks = dict(stand_upright=tilt < np.pi/18, tip_near_base=distance < .05,
                        shaft_between_opposed_walls=all(d < 0 for d in dots))
    endpoint = site('frame_hang_site')
    axis = site('frame_intersection_site') - endpoint
    length = float(np.linalg.norm(axis))
    axis /= length
    touching = any(check_contact(sim, n.robots[0].gripper.important_geoms[key], n.tool.contact_geoms)
                   for key in ['left_fingerpad', 'right_fingerpad'])
    holes = {}
    for hole in [1, 2]:
        names = [f'tool_hole{hole}_hc_{i}' for i in range(n.tool_args['ngeoms'])]
        center = sim.data.site_xpos[sim.model.site_name2id(f'tool_hole{hole}_center')].copy()
        vector = center - endpoint
        along = float(np.dot(vector, axis))
        orthogonal = float(np.linalg.norm(vector - along * axis))
        geoms = [sim.data.geom_xpos[sim.model.geom_name2id(names[i])] for i in [0, n.tool_args['ngeoms']//2]]
        straddle = float(np.dot(np.cross(geoms[0]-endpoint, axis), np.cross(geoms[1]-endpoint, axis)))
        tolerance = n.tool_args[f'inner_radius_{hole}'] - n.frame_args['frame_thickness']/2
        checks = dict(fingerpads_released=not touching,
                      horizontal_hook_contact=bool(check_contact(sim, names, 'frame_horizontal_frame')),
                      center_near_hook_line=orthogonal < tolerance, walls_straddle_hook=straddle < 0,
                      enough_insertion=.05 < along/length < 1)
        holes[str(hole)] = dict(label='larger' if hole == 1 else 'smaller', checks=checks,
                               inner_radius_m=n.tool_args[f'inner_radius_{hole}'],
                               distance_to_hook_line_m=orthogonal, line_tolerance_m=tolerance,
                               insertion_fraction=along/length, all_checks=all(checks.values()))
    native_frame, native_tool = bool(n._check_frame_assembled()), bool(n._check_tool_on_frame())
    native_success, adapter_success = bool(n._check_success()), bool(env.check_success())
    assert native_frame == all(frame_checks.values())
    assert native_tool == holes['1']['all_checks']
    assert native_success == adapter_success == (native_frame and native_tool)
    outcome = json.loads((run / 'outcome.json').read_text())
    if step == count:
        assert native_success == outcome['success']
        assert env.diagnostic_goals() == outcome['diagnostic_goal_predicates']
    result = dict(episode=run.name, step=step, final_state=step == count,
                  frame_pass=native_frame, tool_pass=native_tool, full_pass=native_success,
                  adapter_matches_native=True, final_outcome_matches_native=step == count,
                  frame_checks=frame_checks, frame_tip_to_base_m=distance,
                  maximum_tip_to_base_m=.05, wall_cross_dots=dots, holes=holes)
    env.close()
    return result


local = ROOT / '.venv/lib/python3.11/site-packages/robosuite/environments/manipulation/tool_hang.py'
official = HERE / 'official_tool_hang_v1_4_1.py'
def methods(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.FunctionDef)}
a, b = methods(local), methods(official)
matches = {name: a[name] == b[name] for name in ['_check_success', '_check_frame_assembled', '_check_tool_on_frame']}
assert all(matches.values())
protocol = json.loads((HERE.parent / 'protocol.json').read_text())
rows = [inspect(ROOT / 'runs/pilot_tool_hang_001')]
rows += [inspect(ROOT / 'runs' / trial['episode_id']) for trial in protocol['episodes']]
rows += [inspect(ROOT / 'runs/th_v1_s01_direct_waypoints', 1341),
         inspect(ROOT / 'runs/th_v1_s01_phase_guard', 518),
         inspect(ROOT / 'runs/th_v1_s01_deadline_guard', 1928)]
report = dict(scope='Private saved-state audit of pinned benchmark semantics, not a new policy episode or task-success redefinition.',
              checker_ast_matches_official=matches, samples=rows,
              scorer_source_sha256=hashlib.sha256(local.read_bytes()).hexdigest(),
              audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              reproduce='.venv/bin/python studies/tool_hang_v1/scorer_audit/audit.py',
              limitation='Rebuilt contacts show geometry, not contact forces. Release check covers fingerpads, not every robot link. Native line/depth tolerances can reject visible suspension; report that partial behavior separately.')
(HERE / 'audit.json').write_text(json.dumps(report, indent=2))
for r in rows:
    print(r['episode'], r['step'], 'frame/tool/full', r['frame_pass'], r['tool_pass'], r['full_pass'])
