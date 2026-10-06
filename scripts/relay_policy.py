"""Capture an Astra decision from the root rollout and relay it without alteration.

Read only matching agent messages. Never export the whole desktop session.
"""
import argparse
import json
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--session', required=True)
parser.add_argument('--agent', required=True)
parser.add_argument('--input', required=True)
parser.add_argument('--run', required=True)
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
matches = []
for line in Path(args.session).read_text().splitlines():
    event = json.loads(line)
    item = event.get('payload', {})
    if item.get('type') == 'agent_message' and item.get('author') == args.agent:
        raw = '\n'.join(c.get('text','') for c in item['content'])
        output = raw.split('Payload:\n',1)[1]
        matches.append((event.get('timestamp'), output))
if not matches:
    raise SystemExit('No returned decision from the requested agent')
timestamp, output = matches[-1]
command = json.loads(output)
run = Path(args.run)
n = len(list(run.glob('policy_turn_*.json'))) + 1
body = dict(command=command, policy=dict(model='gpt-6-astra', reasoning_effort='medium',
    agent=args.agent, policy_visible_input=Path(args.input).read_text(),
    raw_output=output, response_timestamp=timestamp,
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
