"""Private geometry context for recorded stops; no policy or executor access."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env


def main():
    samples = []
    protocol = json.loads((HERE / 'protocol.json').read_text())
    for trial in protocol['episodes']:
        run = ROOT / 'runs' / trial['episode_id']
        if not (run / 'outcome.json').exists():
            continue
        commands = [json.loads(line) for line in (run / 'commands.jsonl').read_text().splitlines()]
        stops = [c for c in commands if c['result'].get('execution_report', {}).get(
            'stop_reason') == 'armed_empty_sized_closure']
        if not stops:
            continue
        config = json.loads((run / 'config.json').read_text())
        saved = np.load(run / 'trajectory.npz')
        env, _, _ = make_env(**{k: config[k] for k in
                               ['task', 'suite', 'seed', 'state_index', 'size']})
        sim, gripper = env.sim, env.robots[0].gripper
        pads = {side: set(gripper.important_geoms[side + '_fingerpad'])
                for side in ['left', 'right']}
        for command in stops:
            for step in range(command['result']['step'] - 2, command['result']['step'] + 1):
                sim.set_state_from_flattened(saved['states'][step - 1])
                sim.forward()
                pad_objects = {side: set() for side in pads}
                contacts = []
                for contact in sim.data.contact[:sim.data.ncon]:
                    a, b = [sim.model.geom_id2name(i) for i in
                            [contact.geom1, contact.geom2]]
                    for side, geoms in pads.items():
                        robot, other = (a, b) if a in geoms else (b, a)
                        if robot in geoms and other:
                            contacts.append(dict(side=side, other_geom=other,
                                                 distance_m=float(contact.dist)))
                            for prefix in ['frame', 'tool', 'stand']:
                                if other.startswith(prefix):
                                    pad_objects[side].add(prefix)
                samples.append(dict(episode=run.name, decision=command['call'], step=step,
                                    both_pad_objects=sorted(pad_objects['left'] & pad_objects['right']),
                                    fingerpad_contacts=contacts))
        env.close()
    result = dict(samples=samples, actual_astra_requests=0,
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Private post-episode saved-state diagnosis of three samples ending at each stop.',
                  limitation='Rebuilt contacts are geometry, not forces or a complete acquisition certificate. '
                  'Recovered prefix states were reconstructed from native actions; retained original '
                  'robot/object/scoring records and final RGB-D matched exactly.',
                  reproduce='.venv/bin/python studies/tool_hang_v2/interrupt_diagnosis.py')
    (HERE / 'interrupt_geometry.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
