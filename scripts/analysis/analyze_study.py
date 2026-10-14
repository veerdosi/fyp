"""Descriptive paired results for the frozen ToolHang study, including missing runs."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def wilson(successes, n):
    if not n:
        return None
    z=1.959963984540054
    p=successes/n
    denominator=1+z*z/n
    centre=(p+z*z/(2*n))/denominator
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [max(0,centre-half),min(1,centre+half)]


def analyze(root, path):
    protocol=json.loads(path.read_text())
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    rows=[]
    for trial in protocol['episodes']:
        run=root/'runs'/trial['episode_id']
        row=dict(trial, status='missing', success=None)
        if (run/'outcome.json').exists():
            config=json.loads((run/'config.json').read_text())
            if config.get('frozen_study',{}).get('protocol_sha256') != digest:
                raise ValueError(f'Protocol mismatch: {run.name}')
            if config['source_hashes'] != protocol['source_hashes'] or config['code_dirty']:
                raise ValueError(f'Source mismatch or dirty code: {run.name}')
            assert config['frozen_study']['material_hashes'] == protocol['material_hashes']
            assert config['versions'] == protocol['runtime_versions']
            assert config['execution_criteria'] == protocol['arrival_criteria']
            assert config['model'] == protocol['shared']['model']
            assert config['reasoning_effort'] == protocol['shared']['reasoning_effort']
            for key in ['size','max_steps','max_calls','settle_steps','computation_protocol','calculation_timeout_seconds']:
                assert config[key] == protocol['shared'][key]
            for key in ['task','suite']:
                assert config[key] == protocol[key]
            for key in ['seed','state_index','condition']:
                assert config[key] == trial[key]
            outcome=json.loads((run/'outcome.json').read_text())
            row.update(status='recorded', success=outcome['success'], stop_reason=outcome['stop_reason'],
                       simulated_seconds=outcome['simulated_seconds'], decisions=outcome['model_calls'],
                       total_host_wall_seconds=outcome['wall_seconds'])
            for name in ['policy_usage','diagnostic_summary','replay_verification','causal_review']:
                item=run/(name+'.json')
                row[name]=json.loads(item.read_text()) if item.exists() else None
            if row['policy_usage']:
                row.update(inference_requests=row['policy_usage']['model_inference_requests'],
                           native_policy_turn_seconds=row['policy_usage']['policy_wall_seconds'],
                           api_equivalent_cost_usd=row['policy_usage']['api_equivalent_standard_cost_usd'])
            review_path=run/'policy_tools_complete.json'
            row['boundary_review_present']=(review_path.exists() and
                bool(json.loads(review_path.read_text()).get('manual_boundary_review')))
            row['complete_evidence']=bool(row['policy_usage'] and row['diagnostic_summary'] and
                row['replay_verification'] and row['replay_verification']['pass'] and
                row['causal_review'] and row['boundary_review_present'])
        rows.append(row)
    summaries={}
    for condition in protocol['conditions']:
        subset=[r for r in rows if r['condition']==condition and r['status']=='recorded']
        n=len(subset);wins=sum(r['success'] for r in subset)
        summaries[condition]=dict(recorded_trials=n, planned_trials=protocol['paired_state_count'],
                                  successes=wins, success_rate=wins/n if n else None,
                                  success_rate_wilson_95=wilson(wins,n))
    pairs=[]
    for state in range(1,protocol['paired_state_count']+1):
        subset=[r for r in rows if r['paired_state']==state and r['status']=='recorded']
        if len(subset) != len(protocol['conditions']):
            continue
        states=[np.load(root/'runs'/r['episode_id']/'initial_state.npy') for r in subset]
        assert all(np.array_equal(states[0],s) for s in states[1:]), 'Unmatched initial states'
        baseline=next(r for r in subset if r['condition']=='direct_waypoints')
        for other in subset:
            if other is baseline:
                continue
            pair=dict(paired_state=state, baseline=baseline['episode_id'], comparison=other['episode_id'],
                      condition=other['condition'], success_difference=int(other['success'])-int(baseline['success']),
                      both_succeeded=baseline['success'] and other['success'], matched_initial_state=True)
            for metric in ['decisions','inference_requests','simulated_seconds','native_policy_turn_seconds','api_equivalent_cost_usd']:
                if metric in other and metric in baseline:
                    pair[metric+'_difference']=other[metric]-baseline[metric]
                    if pair['both_succeeded']:
                        pair[metric+'_ratio']=other[metric]/baseline[metric] if baseline[metric] else None
            pairs.append(pair)
    result=dict(study_id=protocol['study_id'], protocol_sha256=digest, trials=rows,
                condition_summaries=summaries, paired_results=pairs,
                complete=all(r.get('complete_evidence',False) for r in rows),
                statistical_scope='Small descriptive paired study: Wilson intervals for observed condition proportions; paired wins/losses and resource differences. No equivalence, generalization or significance claim. Missing evidence is not success.',
                time_scope='Native policy-turn durations, delivered-response delays, execution and total host elapsed are distinct. Simulator physics pauses during inference. Successful-pair resource ratios only; every failed trial remains in success counts.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[2]
    parser.add_argument('--protocol',type=Path,default=root/'studies/tool_hang_v1/protocol.json')
    parser.add_argument('--output',type=Path,default=root/'studies/tool_hang_v1/results.json')
    args=parser.parse_args()
    result=analyze(root,args.protocol)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ['trials','paired_results']},indent=2))
