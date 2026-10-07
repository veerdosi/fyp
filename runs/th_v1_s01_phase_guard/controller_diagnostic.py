"""Private offline joint/contact diagnosis of recorded reorientation states."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

run = Path(__file__).resolve().parent
sys.path.insert(0, str(run.parents[1] / 'src'))
from fyp.runtime import make_env

config = json.loads((run / 'config.json').read_text())
env, _, _ = make_env(**{k: config[k] for k in ['task', 'suite', 'state_index', 'seed', 'size']})
sim, robot = env.sim, env.robots[0]
saved = np.load(run / 'trajectory.npz')
records = [json.loads(line) for line in (run / 'steps.jsonl').read_text().splitlines()]
rows = []
for step in [979, 1079, 1179, 1217, 1218, 1220, 1249, 1250, 1279, 1379, 1479, 1579]:
    env.set_init_state(saved['states'][step-1])
    joints = []
    for name, qi, ji in zip(robot.robot_joints, robot._ref_joint_pos_indexes, robot._ref_joint_indexes):
        angle = float(sim.data.qpos[qi])
        lower, upper = map(float, sim.model.jnt_range[ji])
        joints.append(dict(name=name, angle_rad=angle, lower_rad=lower, upper_rad=upper,
                           nearest_limit_margin_rad=min(angle-lower, upper-angle)))
    contacts = []
    for i in range(sim.data.ncon):
        c = sim.data.contact[i]
        names = [sim.model.geom_id2name(g) for g in (c.geom1, c.geom2)]
        if any(n and n.startswith(('robot0', 'gripper0')) for n in names):
            contacts.append(dict(geom_names=names, distance_m=float(c.dist)))
    rows.append(dict(step=step, command_id=records[step-1]['command_id'],
                     joints=joints, contacts_rebuilt_by_forward=contacts,
                     native_goals=env.diagnostic_goals()))
result = dict(scope='Private diagnosis only. Joint margins and rebuilt contacts are correlates, not proof of pose infeasibility or a replay of contact forces.',
              states=rows, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              reproduce='.venv/bin/python runs/th_v1_s01_phase_guard/controller_diagnostic.py')
(run / 'controller_diagnostic.json').write_text(json.dumps(result, indent=2))
for row in rows:
    print(json.dumps(dict(step=row['step'], joints_near_limit=[j for j in row['joints'] if j['nearest_limit_margin_rad'] < .03],
                          contact_count=len(row['contacts_rebuilt_by_forward']), goals=row['native_goals'])))
env.close()
