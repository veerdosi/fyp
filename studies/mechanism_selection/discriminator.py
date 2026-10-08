"""Private saved-state diagnosis for a predefined mechanism-selection cohort."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'discriminator_protocol.json').read_text())
    assert not (HERE / 'discriminator_result.json').exists()
    samples, source_hashes = [], {}
    episodes = list(dict.fromkeys(x['episode'] for x in protocol['samples']))
    for name in episodes:
        run = ROOT / 'runs' / name
        config = json.loads((run / 'config.json').read_text())
        trajectory = np.load(run / 'trajectory.npz')
        commands = {x['call']: x for x in map(json.loads, (run / 'commands.jsonl').read_text().splitlines())}
        source_hashes[str((run / 'trajectory.npz').relative_to(ROOT))] = sha(run / 'trajectory.npz')
        source_hashes[str((run / 'commands.jsonl').relative_to(ROOT))] = sha(run / 'commands.jsonl')
        env, _, _ = make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
        sim = env.sim
        robot = env.robots[0]
        ranges = np.asarray(robot.robot_model.joints)
        joint_ids = [sim.model.joint_name2id(j) for j in ranges]
        q_indices = [sim.model.jnt_qposadr[j] for j in joint_ids]
        limits = sim.model.jnt_range[joint_ids]
        for selection in [s for s in protocol['samples'] if s['episode']==name]:
            command = commands[selection['decision']]
            report = command['result']['execution_report']
            waypoints = []
            for waypoint in report['waypoints']:
                first, last = waypoint['first_step'], waypoint['last_step']
                minimum_margin = np.full(7, np.inf)
                contact_names = set()
                contact_steps = 0
                terminal_q = None
                for step in range(first, last+1):
                    sim.set_state_from_flattened(trajectory['states'][step-1])
                    sim.forward()
                    q = sim.data.qpos[q_indices].copy()
                    margin = np.minimum(q-limits[:,0], limits[:,1]-q)
                    minimum_margin = np.minimum(minimum_margin, margin)
                    occupied = False
                    for contact in sim.data.contact[:sim.data.ncon]:
                        names = [sim.model.geom_id2name(i) or '' for i in [contact.geom1,contact.geom2]]
                        flags = [s.startswith(('robot0_', 'gripper0_', 'mount0_')) for s in names]
                        if flags[0] == flags[1]:
                            continue
                        # Exclude robot mount/floor contacts; retain task/table pairs.
                        other = names[1] if flags[0] else names[0]
                        if other in {'floor','world',''}:
                            continue
                        contact_names.add(tuple(names))
                        occupied = True
                    contact_steps += int(occupied)
                    terminal_q = q
                index = waypoint['waypoint_index']
                waypoints.append(dict(index=index,first_step=first,last_step=last,
                    terminal_measurement=waypoint['terminal_measurement'],
                    resolved_target_quaternion=waypoint['resolved_quaternion_xyzw'],
                    target_position=command['command']['waypoints'][index]['position'],
                    minimum_joint_limit_margin_rad=minimum_margin.tolist(),
                    minimum_margin_rad=float(min(minimum_margin)),
                    terminal_joint_position_rad=terminal_q.tolist(),
                    robot_nonrobot_contact_geometry_steps=contact_steps,
                    contact_geometry_pairs=[list(x) for x in sorted(contact_names)]))
            before = json.loads((run / 'public' / f"obs_{command['input_observation_id']:04d}" / 'observation.json').read_text())
            samples.append(dict(**selection, reason=command['command'].get('reason'),
                public_robot_measurement_keys=list(before['proprioception']),waypoints=waypoints))
        env.close()
    calculations = []
    for name in ['th_v2_s01_guard','th_v2_s02_guard']:
        for folder in sorted((ROOT / 'runs' / name / 'policy_calculation_logs').glob('calc_*')):
            calculations.append(dict(episode=name,calculation=folder.name,
                code_sha256=sha(folder/'code.py'),output_sha256=sha(folder/'stdout.txt'),
                output=(folder/'stdout.txt').read_text(),
                returncode=json.loads((folder/'metadata.json').read_text())['returncode']))
    result = dict(protocol_sha256=sha(HERE/'discriminator_protocol.json'),
        code_sha256=sha(Path(__file__)),source_hashes=source_hashes,samples=samples,
        calculations=calculations,actual_astra_requests=0,
        scope='Private saved-state geometry only. Does not reconstruct forces or establish causal attribution.',
        reproduce='.venv/bin/python studies/mechanism_selection/discriminator.py (preserve prior result first)')
    (HERE / 'discriminator_result.json').write_text(json.dumps(result,indent=2)+'\n')
    for sample in samples:
        print(sample['episode'],sample['decision'],[(w['index'],round(w['minimum_margin_rad'],4),
            w['robot_nonrobot_contact_geometry_steps']) for w in sample['waypoints']],flush=True)


if __name__ == '__main__':
    main()
