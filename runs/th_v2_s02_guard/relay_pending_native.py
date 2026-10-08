"""Relay the already-returned decision missing from the interrupted root mailbox."""
import json
import urllib.request
from pathlib import Path

run = Path(__file__).resolve().parent
import argparse
parser = argparse.ArgumentParser(); parser.add_argument('--turn', required=True); parser.add_argument('--decision', type=int, required=True); args = parser.parse_args()
link = json.loads((run/'operator_link.json').read_text())
events = [json.loads(line) for line in Path(link['policy_session']).read_text().splitlines()]
event = next(e for e in events if e.get('payload', {}).get('type') == 'task_complete' and e['payload']['turn_id'] == args.turn)
payload = event['payload']
output = payload['last_agent_message']
message_id = 'native_task_complete:' + payload['turn_id']
for path in run.glob('policy_turn_*.json'):
    assert json.loads(path.read_text()).get('policy',{}).get('message_id') != message_id, 'Already executed'
assert len(list(run.glob('policy_turn_*.json'))) == args.decision - 1
body = dict(command=json.loads(output), policy=dict(model='gpt-6-astra', reasoning_effort='medium',
    agent=link['policy_agent'], policy_visible_input=(run/f'policy_update_{args.decision:03d}.txt').read_text(),
    raw_output=output, response_timestamp=event['timestamp'], message_id=message_id,
    dispatch_timestamp=None, policy_wall_seconds=None, native_policy_seconds=payload['duration_ms']/1000, policy_clock_note='Delivery interval unavailable for mailbox recovery; native duration recorded separately.',
    input_file=str(run/f'policy_update_{args.decision:03d}.txt'), native_source_session=link['policy_session'],
    native_source_ordinal=event['ordinal'], recovery_note='Exact completed native policy output; root mailbox delivery lost during interruption. No new inference or command alteration. Native turn duration recorded separately; missing dispatch/delivery interval is not zero inference time.'))
path = run/f'relay_{args.decision:03d}.json'
path.write_text(json.dumps(body, indent=2))
request = urllib.request.Request('http://127.0.0.1:8765/command', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request, timeout=180) as response:
    result = response.read().decode()
path.with_suffix('.result.json').write_text(result)
print(result)
