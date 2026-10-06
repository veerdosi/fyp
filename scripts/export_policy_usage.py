"""Export measured usage for one robot agent, without exporting its private reasoning."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--agent-session', required=True)
parser.add_argument('--run', required=True)
args=parser.parse_args()
records=[]
contexts={}
turns={}
seen=set()
tool_calls=0
for line in Path(args.agent_session).read_text().splitlines():
    event=json.loads(line)
    q=event.get('payload',{})
    if event['type']=='turn_context':
        contexts[q['turn_id']]={'model':q.get('model'),'effort':q.get('effort')}
    if event['type']=='token_usage_record':
        if q['response_id'] in seen:
            continue
        seen.add(q['response_id'])
        records.append(dict(timestamp=event['timestamp'],turn_id=q['turn_id'],
                            response_id=q['response_id'],usage=q['usage']))
    if q.get('type')=='task_complete':
        turns[q['turn_id']]={k:q.get(k) for k in
                             ['started_at','completed_at','duration_ms','time_to_first_token_ms']}
    if q.get('type') in ['function_call','custom_tool_call']:
        tool_calls+=1
if any(c!={'model':'gpt-6-astra','effort':'medium'} for c in contexts.values()):
    raise SystemExit('Unexpected robot policy model or effort in source session')
totals={k:sum(r['usage'].get(k,0) for r in records) for k in
        ['input_tokens','cached_input_tokens','cache_write_input_tokens',
         'output_tokens','reasoning_output_tokens','total_tokens']}
cost=0
for r in records:
    u=r['usage']
    cached=u.get('cached_input_tokens',0)
    writes=u.get('cache_write_input_tokens',0)
    uncached=u['input_tokens']-cached-writes
    if uncached<0:
        raise SystemExit('Inconsistent input token subtotals')
    long_context=u['input_tokens']>272000
    input_multiplier=2 if long_context else 1
    output_multiplier=1.5 if long_context else 1
    cost+=(input_multiplier*(uncached*10+cached*1+writes*12.5)+
           output_multiplier*u['output_tokens']*50)/1e6
run=Path(args.run)
summary=dict(model='gpt-6-astra',reasoning_effort='medium',
             policy_decisions=len(list(run.glob('policy_turn_*.json'))),
             model_inference_requests=len(records),agent_tool_calls=tool_calls,
             completed_policy_turns=len(turns),
             policy_wall_seconds=sum(t['duration_ms'] or 0 for t in turns.values())/1000,
             token_usage=totals,api_equivalent_standard_cost_usd=round(cost,6),
             actual_account_charge_usd=None,
             pricing=dict(source='https://developers.openai.com/api/docs/models/gpt-6-astra',
                          accessed_date='2026-10-06',per_million_tokens_usd=
                          dict(uncached_input=10,cached_input=1,cache_write=12.5,output=50),
                          assumption='Standard API rates; native account tier/speed/billing is unknown'),
             cost_note='An API-equivalent estimate from measured token records, not an account charge.',
             source_session=str(Path(args.agent_session).resolve()),
             model_effort_verification=contexts,turn_timing=turns)
(run/'policy_usage_records.json').write_text(json.dumps(records,indent=2))
(run/'policy_usage.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['model_effort_verification','turn_timing']},indent=2))
