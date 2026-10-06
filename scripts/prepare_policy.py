"""Create the sensor-only initial policy prompt for a new direct-control episode."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('run')
args=parser.parse_args()
run=Path(args.run).resolve()
config=json.loads((run/'config.json').read_text())
obs=json.loads((run/'public/latest.json').read_text())
if obs['model_calls']!=0:
    raise SystemExit('Initial prompt requires an episode with no policy decision executed')
root=Path(__file__).resolve().parents[1]
template=(root/'runs/pilot_microwave_001/policy_initial.txt').read_text()
prefix=template.split('\nCurrent observation 0, step 0:',1)[0]
prefix=prefix.replace('pilot_microwave_001',run.name)
if config['condition']=='direct_pose':
    prefix=prefix.replace('One to four waypoints','Exactly one waypoint')
    prefix=prefix.replace('One to four','Exactly one')
message=(prefix+f'\nCurrent observation {obs["observation_id"]}, step {obs["step"]}, '
         f'simulated time {obs["simulated_seconds"]} seconds: robot sensors '+
         json.dumps(obs['proprioception'])+'.\n\n'+
         f'Current public observation folder: {obs["folder"]}. Images: '+
         ' and '.join(obs['cameras'].values())+'. '+
         'The observation.json and calibration.json in that folder contain the full permitted readings and calibration. '+
         f'{obs["remaining_steps"]} control steps and {obs["remaining_model_calls"]} policy decisions remain. '+
         'Interpret these images and return the next command.')
(run/'policy_initial.txt').write_text(message)
print(message)
