"""Capture an Astra decision from the root rollout and relay it without alteration.

Read only matching agent messages. Never export the whole desktop session.
"""
import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--session', required=True)
parser.add_argument('--agent', required=True)
parser.add_argument('--input', required=True)
parser.add_argument('--run', required=True)
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
matches = []
dispatches = []
for line in Path(args.session).read_text().splitlines():
    event = json.loads(line)
    item = event.get('payload', {})
    if item.get('type')=='function_call' and item.get('namespace')=='collaboration' and item.get('name') in ['spawn_agent','followup_task']:
        params=json.loads(item['arguments'])
        target=params.get('target',params.get('task_name',''))
        if target==args.agent or target==args.agent.split('/')[-1]:
            dispatches.append(event.get('timestamp'))
    if item.get('type') == 'agent_message' and item.get('author') == args.agent:
        raw = '\n'.join(c.get('text','') for c in item['content'])
        output = raw.split('Payload:\n',1)[1]
        matches.append((event.get('timestamp'), item.get('id'), output))
if not matches:
    raise SystemExit('No returned decision from the requested agent')
timestamp, message_id, output = matches[-1]
command = json.loads(output)
run = Path(args.run)
for previous in run.glob('relay_*.json'):
    if previous.name.endswith('.result.json'):
        continue
    if json.loads(previous.read_text()).get('policy',{}).get('message_id')==message_id:
        raise SystemExit('This returned decision has already been relayed; inspect its saved result')
n = len(list(run.glob('policy_turn_*.json'))) + 1
dispatch_timestamp=dispatches[-1] if dispatches else None
policy_wall_seconds=None
if timestamp and dispatch_timestamp:
    policy_wall_seconds=(datetime.fromisoformat(timestamp.replace('Z','+00:00'))-
                         datetime.fromisoformat(dispatch_timestamp.replace('Z','+00:00'))).total_seconds()
body = dict(command=command, policy=dict(model='gpt-6-astra', reasoning_effort='medium',
    agent=args.agent, policy_visible_input=Path(args.input).read_text(),
    raw_output=output, response_timestamp=timestamp, message_id=message_id,
    dispatch_timestamp=dispatch_timestamp, policy_wall_seconds=policy_wall_seconds,
    input_file=str(Path(args.input).resolve())))
path = run / f'relay_{n:03d}.json'
path.write_text(json.dumps(body, indent=2))
request = urllib.request.Request(f'http://127.0.0.1:{args.port}/command',
                                 data=json.dumps(body).encode(),
                                 headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request, timeout=180) as response:
    result=response.read().decode()
path.with_suffix('.result.json').write_text(result)
print(result)
