"""Create the sensor-only initial policy prompt for a new direct-control episode."""
import argparse
import json
import re
from pathlib import Path
from policy_access import computation_access

parser=argparse.ArgumentParser()
parser.add_argument('run')
args=parser.parse_args()
run=Path(args.run).resolve()
config=json.loads((run/'config.json').read_text())
obs=json.loads((run/'public/latest.json').read_text())
if obs['model_calls']!=0:
    raise SystemExit('Initial prompt requires an episode with no policy decision executed')
root=Path(__file__).resolve().parents[1]
prefix=(root/'docs/policy_prompt_template.txt').read_text().rstrip()
prefix=prefix.replace('pilot_microwave_001',run.name)
if config['suite'] == 'robosuite':
    import sys
    sys.path.insert(0, str(root/'src'))
    from fyp.robosuite_runtime import TASK_INSTRUCTIONS
    language=TASK_INSTRUCTIONS[config['task']]
    prefix=prefix.replace('standard LIBERO Panda robot', 'standard robosuite Panda robot')
else:
    bddl=root/'vendor/LIBERO/libero/libero/bddl_files'/config['suite']/(config['task']+'.bddl')
    language=re.search(r'\(:language\s+([^\n]+)\)', bddl.read_text()).group(1).strip()
language=language.rstrip('.')
prefix=re.sub(r'Task: .*?\. Control the standard',
              f'Task: {language}. Control the standard', prefix, count=1)
prefix=prefix.replace('You decide object selection, grasp, transport, placement, door closure, recovery and completion.',
                      'You decide object selection, grasp, transport, placement, recovery and completion.')
if config['condition']=='direct_pose':
    prefix=prefix.replace('One to four waypoints','Exactly one waypoint')
    prefix=prefix.replace('One to four','Exactly one')
message=(prefix+'\n\n'+computation_access(run)+f'\n\nCurrent observation {obs["observation_id"]}, step {obs["step"]}, '
         f'simulated time {obs["simulated_seconds"]} seconds: robot sensors '+
         json.dumps(obs['proprioception'])+'.\n\n'+
         f'Current public observation folder: {obs["folder"]}. Images: '+
         ' and '.join(obs['cameras'].values())+'. '+
         'The observation.json and calibration.json in that folder contain the full permitted readings and calibration. '+
         f'{obs["remaining_steps"]} control steps and {obs["remaining_model_calls"]} policy decisions remain. '+
         'Interpret these images and return the next command.')
(run/'policy_initial.txt').write_text(message)
print(message)
