"""Return only the current policy-visible result and unchanged query semantics."""
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
run=Path(sys.argv[1]).resolve()
n=len(list(run.glob('policy_turn_*.json')))
reply=json.loads((run/f'relay_{n:03d}.result.json').read_text())
if reply.get('preview_file') and not reply.get('episode_stopped'):
    text=(f'Your pose calculation is in {reply["preview_file"]}. Read it before selecting the next command. '
        f'No motion occurred; observation {reply["observation_id"]} and its images remain current. '
        f'{reply["remaining_model_calls"]} decisions and {reply["remaining_steps"]} control steps remain. '
        'A bounded solution is not collision clearance or task success. You choose the next motion or query. Return one JSON command only.')
    (run/f'policy_update_{n+1:03d}.txt').write_text(text)
    print(text)
else:
    sys.argv=[str(ROOT/'scripts/prepare_handoff.py'),str(run)]
    runpy.run_path(str(ROOT/'scripts/prepare_handoff.py'),run_name='__main__')
