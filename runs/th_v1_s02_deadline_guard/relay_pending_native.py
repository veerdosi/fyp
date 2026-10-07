"""Relay the already-returned decision missing from the interrupted root mailbox."""
import json
import urllib.request
from pathlib import Path

run = Path(__file__).resolve().parent
link = json.loads((run/'operator_link.json').read_text())
events = [json.loads(line) for line in Path(link['policy_session']).read_text().splitlines()]
event = next(e for e in events if e.get('payload', {}).get('type') == 'task_complete' and e['payload']['turn_id'] == '01a1141e-4faa-78e1-9c42-5a955dea0443')
payload = event['payload']
output = payload['last_agent_message']
message_id = 'native_task_complete:' + payload['turn_id']
for path in run.glob('policy_turn_*.json'):
    assert json.loads(path.read_text()).get('policy',{}).get('message_id') != message_id, 'Already executed'
assert len(list(run.glob('policy_turn_*.json'))) == 3
body = dict(command=json.loads(output), policy=dict(model='gpt-6-astra', reasoning_effort='medium',
    agent=link['policy_agent'], policy_visible_input=(run/'policy_update_004.txt').read_text(),
    raw_output=output, response_timestamp=event['timestamp'], message_id=message_id,
    dispatch_timestamp='2026-10-07T02:08:13.257Z', policy_wall_seconds=payload['duration_ms']/1000,
    input_file=str(run/'policy_update_004.txt'), native_source_session=link['policy_session'],
    native_source_ordinal=event['ordinal'], recovery_note='Exact completed native policy output; root mailbox delivery lost during interruption. No new inference or command alteration. Native turn duration recorded in policy_wall_seconds.'))
path = run/'relay_004.json'
path.write_text(json.dumps(body, indent=2))
request = urllib.request.Request('http://127.0.0.1:8765/command', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request, timeout=180) as response:
    result = response.read().decode()
path.with_suffix('.result.json').write_text(result)
print(result)
