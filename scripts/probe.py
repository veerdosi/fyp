import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fyp.runtime import make_env, proprio, sensor_images, ROOT

env, obs, initial = make_env()
out = ROOT / 'runs/sensor_probe'
out.mkdir(parents=True, exist_ok=True)
from PIL import Image
for name, (rgb, depth) in sensor_images(env, obs).items():
    Image.fromarray(rgb).save(out / (name + '.png'))
audit = {'raw_observations': {k: list(v.shape) for k, v in obs.items()},
         'allowed_proprioception': proprio(obs),
         'controller': {k: str(v) for k, v in vars(env.robots[0].controller).items()
                        if k in ['input_max', 'input_min', 'output_max', 'output_min',
                                 'use_delta', 'control_freq', 'control_dim']},
         'initial_state_shape': list(initial.shape),
         'sensors_in_xml': str(env.sim.model._model.sensor_type),
         'available_sensor_names': [env.sim.model.sensor_id2name(i)
                                    for i in range(env.sim.model.nsensor)]}
(out / 'audit.json').write_text(json.dumps(audit, indent=2))
print(json.dumps(audit, indent=2))
env.close()
