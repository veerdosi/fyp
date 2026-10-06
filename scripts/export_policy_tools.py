"""Export exact policy tool invocations without private reasoning or other sessions.

This creates evidence for manual boundary review; it does not certify compliance.
Calculation source and outputs are separately retained by policy_calc.py.
"""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--agent-session', required=True, type=Path)
parser.add_argument('--run', required=True, type=Path)
args = parser.parse_args()
source = args.agent_session.read_bytes()
calls = []
for line in source.decode().splitlines():
    event = json.loads(line)
    payload = event.get('payload', {})
    if event['type'] == 'turn_context':
        if payload.get('model') != 'gpt-6-astra' or payload.get('effort') != 'medium':
            raise SystemExit('Unexpected policy model or effort')
    if payload.get('type') in ['function_call', 'custom_tool_call']:
        calls.append({'timestamp': event['timestamp'], **{
            k: payload[k] for k in ['type', 'namespace', 'name', 'call_id', 'arguments', 'input']
            if k in payload}})
result = {'source_session': str(args.agent_session.resolve()),
          'source_sha256_at_export': hashlib.sha256(source).hexdigest(),
          'tool_call_count': len(calls), 'tool_calls': calls,
          'review_status': 'Export only; inspect tool inputs and calculation logs for boundary compliance.'}
(args.run / 'policy_tools_complete.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != 'tool_calls'}, indent=2))
