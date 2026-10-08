"""Diagnose final tool support beyond the benchmark's fingerpad release test."""
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
    for trial in json.loads((HERE / 'protocol.json').read_text())['episodes']:
        run = ROOT / 'runs' / trial['episode_id']
        if not (run / 'outcome.json').exists():
            continue
        config = json.loads((run / 'config.json').read_text())
        saved = np.load(run / 'trajectory.npz')
        env, _, _ = make_env(**{k: config[k] for k in
                               ['task', 'suite', 'seed', 'state_index', 'size']})
        sim = env.sim
        sim.set_state_from_flattened(saved['states'][-1])
        sim.forward()
        contacts = []
        for contact in sim.data.contact[:sim.data.ncon]:
            a, b = [sim.model.geom_id2name(i) for i in [contact.geom1, contact.geom2]]
            if not a or not b or not (a.startswith('tool') or b.startswith('tool')):
                continue
            tool, other = (a, b) if a.startswith('tool') else (b, a)
            contacts.append(dict(tool_geom=tool, other_geom=other,
                                 other_robot=other.startswith(('robot0_', 'gripper0_', 'mount0_')),
                                 distance_m=float(contact.dist)))
        samples.append(dict(episode=run.name, step=len(saved['states']), contacts=contacts))
        env.close()
    result = dict(samples=samples, actual_astra_requests=0,
                  scope='Private terminal saved-state contact geometry; no policy/executor access.',
                  limitation='Contacts do not reconstruct forces or prove which contact carries weight. '
                  'The frozen native success criterion remains unchanged.',
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  reproduce='.venv/bin/python studies/tool_hang_v2/support_diagnosis.py')
    (HERE / 'terminal_support_geometry.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
