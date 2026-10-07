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

def describe():
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
    base = sim.data.geom_xpos[native.obj_geom_id['stand_base']].copy()
    stand_axis = sim.data.site_xpos[native.obj_site_id['stand_mount_site']] - base
    stand_axis /= np.linalg.norm(stand_axis)
    angle = float(np.arccos(np.clip(stand_axis[2], -1, 1)))
    tip_name = 'frame_tip_site' if 'frame_tip_site' in native.obj_site_id else 'frame_mount_site'
    tip = sim.data.site_xpos[native.obj_site_id[tip_name]].copy()
    insertion_distance = float(np.linalg.norm(tip-base))
    rod_start = sim.data.site_xpos[native.obj_site_id['frame_mount_site']].copy()
    rod_axis = sim.data.site_xpos[native.obj_site_id['frame_intersection_site']] - rod_start
    rod_axis /= np.linalg.norm(rod_axis)
    walls = [sim.data.geom_xpos[native.obj_geom_id[f'stand_wall_{i}']] - rod_start for i in range(4)]
    wall_dots = [float(np.dot(np.cross(walls[i],rod_axis), np.cross(walls[i+2],rod_axis))) for i in range(2)]
    frame_checks = dict(stand_shaft_upright=bool(angle < np.pi/18),
                        frame_tip_close_to_base=bool(insertion_distance < 0.05),
                        rod_between_opposed_stand_walls=all(d < 0 for d in wall_dots))
    frame_result = dict(checks=frame_checks, all_checks=all(frame_checks.values()),
                        stand_tilt_degrees=float(np.rad2deg(angle)), maximum_stand_tilt_degrees=10,
                        frame_tip_to_base_m=insertion_distance, maximum_tip_distance_m=0.05,
                        opposed_wall_cross_dots=wall_dots, frame_tip_xyz=tip.tolist(), stand_base_xyz=base.tolist())
    return dict(frame=frame_result, holes=holes, native_goals=env.diagnostic_goals())

samples=[]
for step in [465,490,543,1010,1024,1049,1129,1189,1289,1389]:
    env.set_init_state(trajectory["states"][step-1])
    sample=describe()
    sample["step"]=step
    sample["rebuilt_tool_robot_contacts"]=[]
    for contact in sim.data.contact[:sim.data.ncon]:
        names=[sim.model.geom_id2name(int(g)) or "" for g in [contact.geom1,contact.geom2]]
        if any(n.startswith("tool_") for n in names) and any(n.startswith(("robot0_","gripper0_")) for n in names):
            sample["rebuilt_tool_robot_contacts"].append(dict(geoms=names,distance_m=float(contact.dist)))
    samples.append(sample)
result=dict(scope="Private offline saved-state diagnosis; rebuilt contacts give geometry, not forces. Never a policy input.", samples=samples, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), reproduce=f".venv/bin/python runs/{run.name}/placement_diagnostic.py")
(run/"placement_diagnostic.json").write_text(json.dumps(result,indent=2))
for s in samples:
    h=s["holes"]["1"]
    print(s["step"],"frame",s["frame"]["checks"],s["frame"]["frame_tip_to_base_m"],"hole",h["checks"],h["distance_to_hook_line_m"],h["insertion_fraction"],"robotcontacts",s["rebuilt_tool_robot_contacts"])
env.close()
