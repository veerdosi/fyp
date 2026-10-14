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
root=Path(__file__).resolve().parents[2]
prefix=(root/'docs/policy_prompt_template.txt').read_text().rstrip()
prefix=prefix.replace('pilot_tool_hang_001',run.name)
if config['suite'] != 'robosuite':
    raise SystemExit('Only native robosuite policy episodes are active')
import sys
sys.path.insert(0, str(root/'src'))
from fyp.robosuite_runtime import TASK_INSTRUCTIONS
language=TASK_INSTRUCTIONS[config['task']]
language=language.rstrip('.')
prefix=re.sub(r'Task: .*?\. Control the standard',
              f'Task: {language}. Control the standard', prefix, count=1)
prefix=prefix.replace('You decide object selection, grasp, transport, placement, door closure, recovery and completion.',
                      'You decide object selection, grasp, transport, placement, recovery and completion.')
if config['condition']=='direct_pose':
    prefix=prefix.replace('One to four waypoints','Exactly one waypoint')
    prefix=prefix.replace('One to four','Exactly one')
if config['condition'] in ['deadline_guard','phase_guard']:
    from sys import path
    path.insert(0, str(root/'src'))
    from fyp.motion import ARRIVAL
    behavior = ('A waypoint may finish early once arrival and settling pass, then execution advances to your next waypoint.'
                if config['condition']=='phase_guard' else
                'Every waypoint still runs its full specified duration; arrival and settling are tested only at its end.')
    prefix=prefix.replace('Each waypoint runs its full specified number of 20Hz steps, 1..100;',
                          'Each waypoint has a maximum duration of 1..100 steps at 20Hz;')
    prefix=prefix.replace('execution does not stop adaptively or decide a new target.',
                          'the executor never decides a new target. '+behavior+
                          ' If arrival and settling fail at the waypoint deadline, the remaining waypoints are cancelled and you receive fresh observations to choose recovery. '+
                          'Criteria: '+json.dumps(ARRIVAL)+'. Settling requires consecutive samples passing all pose/speed limits. '+
                          'The minimum_steps is a lower bound for early completion; a shorter deadline will fail it. '+
                          'Robot arrival does not establish grasp acquisition or placement success.')
prefix += '\nAfter each move, an execution.json report gives the same derived robot pose/speed measurements in every condition. It is not an object or task-success signal.'
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
