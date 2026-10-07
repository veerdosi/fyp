"""Private diagnosis of seating and withdrawal in the verified interrupted prefix."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

run = Path(__file__).resolve().parent
sys.path.insert(0, str(run.parents[1]/'src'))
from fyp.runtime import make_env

assert json.loads((run/'prefix_checkpoint_verification.json').read_text())['pass_verification']
saved = np.load(run/'interruption_checkpoint.npz')
config = json.loads((run/'config.json').read_text())
env, _, _ = make_env(**{k:config[k] for k in ['task','suite','state_index','seed','size']})
native = env.env
sim = native.sim
samples = []
for step in [355,405,470,570,575,580,585,590,595,610,810,950,1020,1055,1090,1115,1180,1260,1325,1525,1685]:
    env.set_init_state(saved['states'][step-1])
    base = sim.data.geom_xpos[native.obj_geom_id['stand_base']].copy()
    stand_axis = sim.data.site_xpos[native.obj_site_id['stand_mount_site']]-base
    stand_axis /= np.linalg.norm(stand_axis)
    tip_name = 'frame_tip_site' if 'frame_tip_site' in native.obj_site_id else 'frame_mount_site'
    tip = sim.data.site_xpos[native.obj_site_id[tip_name]].copy()
    origin = sim.data.site_xpos[native.obj_site_id['frame_mount_site']].copy()
    rod = sim.data.site_xpos[native.obj_site_id['frame_intersection_site']]-origin
    rod /= np.linalg.norm(rod)
    walls = [sim.data.geom_xpos[native.obj_geom_id[f'stand_wall_{i}']]-origin for i in range(4)]
    dots = [float(np.dot(np.cross(walls[i],rod), np.cross(walls[i+2],rod))) for i in range(2)]
    tilt = float(np.arccos(np.clip(stand_axis[2],-1,1)))
    distance = float(np.linalg.norm(tip-base))
    contacts = []
    for contact in sim.data.contact[:sim.data.ncon]:
        names = [sim.model.geom_id2name(int(g)) for g in [contact.geom1,contact.geom2]]
        if any((n or '').startswith('frame_') for n in names):
            contacts.append(dict(geoms=names,distance_m=float(contact.dist)))
    samples.append(dict(step=step, native_goals=env.diagnostic_goals(),
                        stand_tilt_degrees=float(np.rad2deg(tilt)), frame_tip_to_base_m=distance,
                        opposed_wall_cross_dots=dots, tip_xyz=tip.tolist(), stand_base_xyz=base.tolist(),
                        frame_checks=dict(stand_upright=bool(tilt<np.pi/18), tip_near_base=distance<.05,
                                          shaft_between_walls=all(d<0 for d in dots)),
                        rebuilt_frame_contacts=contacts))
source = Path(sys.modules[native.__class__.__module__].__file__)
result = dict(scope='Private offline prefix diagnosis, not a finished task outcome or a policy input.',
              control_steps=len(saved['actions']), samples=samples,
              limits=dict(stand_tilt_degrees=10, tip_distance_m=.05, wall_cross_dot_max=0),
              contact_note='Contacts rebuilt by simulator forward at saved states; no contact forces inferred.',
              checkpoint_sha256=hashlib.sha256((run/'interruption_checkpoint.npz').read_bytes()).hexdigest(),
              scorer_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              reproduce=f'.venv/bin/python runs/{run.name}/prefix_assembly_diagnostic.py')
(run/'prefix_assembly_diagnostic.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='samples'}))
for s in samples[:6]:
    print(s['step'],s['frame_tip_to_base_m'],s['frame_checks'],s['rebuilt_frame_contacts'])
env.close()
