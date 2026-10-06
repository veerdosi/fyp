"""Prepare a sensor-only follow-up message for an existing episode policy."""
import argparse
import json
from pathlib import Path
from policy_access import computation_access

parser=argparse.ArgumentParser()
parser.add_argument('run')
parser.add_argument('--amend-access', action='store_true')
args=parser.parse_args()
r=Path(args.run).resolve()
n=len(list(r.glob('policy_turn_*.json')))
reply=json.loads((r/f'relay_{n:03d}.result.json').read_text())
if 'validation_error' in reply or 'error' in reply:
    message=f'Your command was rejected: {reply}. Return a valid next command as one JSON object only.'
elif 'points' in reply:
    current=json.loads((r/'public/latest.json').read_text())
    folder=Path(current['folder'])
    sense=folder/f'sense_{n:03d}.json'
    sense.write_text(json.dumps(reply,indent=2))
    message=(f'Your sensing reply is in {sense}. You may cat this permitted sensor result file. '
             f'The images and robot readings in {folder.name} remain current; no motion has occurred. '
             f'{n} decisions have been executed, with {reply["remaining_model_calls"]} remaining. '
             'Return your next command as one JSON object only.')
elif 'folder' in reply:
    folder=Path(reply['folder'])
    message=(f'Fresh observation {reply["observation_id"]} after your motion command, '
             f'step {reply["step"]}, simulated time {reply["simulated_seconds"]} seconds. '
             f'{n} decisions have been executed; {reply["remaining_model_calls"]} model decisions '
             f'and {reply["remaining_steps"]} control steps remain. '
             f'Read the permitted robot readings in {folder}/observation.json. '
             f'Inspect {folder}/agentview.png and {folder}/robot0_eye_in_hand.png. '
             'These replace the prior images. Earlier public snapshots remain available for calculations. '
             'Return the next command as one JSON object only.')
else:
    raise SystemExit('Episode finished; no further handoff needed')
if args.amend_access:
    message = computation_access(r) + '\n\n' + message
(r/f'policy_update_{n+1:03d}.txt').write_text(message)
print(message)
