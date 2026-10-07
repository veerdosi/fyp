"""Verify causal endpoint/availability completeness and report predefined gates."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read_rows(name):
    with gzip.open(HERE/name,'rt') as handle:
        return [json.loads(line) for line in handle]


def main():
    result = json.loads((HERE/'accuracy_result.json').read_text())
    protocol = result['protocol']
    cohort = json.loads((ROOT/'studies/object_feedback_feasibility/cohort.json').read_text())
    rows = read_rows('endpoint_samples.jsonl.gz')
    ledger = read_rows('availability.jsonl.gz')
    update_data = json.loads((HERE/'accuracy_updates.json').read_text())
    reconstruction = json.loads((HERE/'accuracy_reconstruction.json').read_text())
    def key(r):
        return r['episode'],r['query_decision'],r['pixel_index'],r['step']
    assert len({key(r) for r in ledger}) == len(ledger)
    assert len({key(r) for r in rows}) == len(rows)
    fresh_keys = {key(r) for r in ledger if r['fresh']}
    assert fresh_keys == {key(r) for r in rows}
    assert all(r['current_world_xyz'] is None for r in ledger if not r['fresh'])
    assert all(r['last_endpoint_age_steps']==0 for r in ledger if r['fresh'])
    expected = set()
    for s in cohort['streams']:
        for p in s['points']:
            for step in range(s['start_step']+1,s['end_step']+1):
                expected.add((s['episode'],p['query_decision'],p['pixel_index'],step))
    assert expected == {key(r) for r in ledger}
    for u in update_data['updates']:
        assert u['output_frame'] == u['last_input_frame']
        assert u['no_future_inputs'] and u['tracks_shape'][1] == u['output_frame']+1
        assert 9 <= u['last_input_frame']-u['first_input_frame']+1 <= 16
        if u['bootstrap']:
            assert u['first_input_frame']==0 and u['last_input_frame']==15
    assert all(c[k] for c in reconstruction['checks'] for k in ['rgb_exact','depth_exact','calibration_exact'])
    assert all(c['max_state_absolute_error']==0 for c in reconstruction['replay_checks'])
    assert len(rows)==result['expected_endpoint_samples'] and len(ledger)==result['expected_availability_samples']
    assert len(result['initial_queries']) == 212
    expected_categories = {k:{str(s[k]) for s in cohort['streams']} for k in ['motion_type','paired_state','condition']}
    for k, values in expected_categories.items():
        assert values == set(result['groups'][k])
    # Occlusion is a safety proxy; preserve its failed gate and diagnose the
    # actual geometric error too, without changing acceptance or thresholds.
    error_groups = {}
    for name, subset in [('visible',[r for r in rows if r['reference_visible'] is True]),
                         ('occluded',[r for r in rows if r['reference_visible'] is False]),
                         ('all_known',[r for r in rows if r['reference_visible'] is not None])]:
        errors=[r['world_error_m'] for r in subset if r['accepted']]
        error_groups[name]=dict(accepted=len(errors),over_3mm=sum(e>.003 for e in errors),
            error_p95_m=float(np.percentile(errors,95)) if errors else None,
            error_max_m=max(errors,default=None))
    (HERE/'accuracy_error_diagnostic.json').write_text(json.dumps(dict(
        scope='Post-result diagnosis; original gates and cohort unchanged.',groups=error_groups),indent=2)+'\n')
    known=sum(p['reference_available'] for p in result['initial_queries'])
    verification=dict(all_pass=True,queries=212,known_initial_references=known,unknown_initial_references=212-known,
        original_streams=len(cohort['streams']),camera_streams=len(reconstruction['checks']),
        endpoint_rows=len(rows),availability_rows=len(ledger),local_tracker_forward_calls=len(update_data['updates']),
        exact_replayed_steps=sum(c['steps'] for c in reconstruction['replay_checks']),
        all_control_frames_retained=True,no_future_endpoint_scoring=True,no_stale_point_presented_as_current=True,
        source_hashes_still_match=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in protocol['source_hashes'].items()),
        output_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['accuracy_result.json','endpoint_samples.jsonl.gz','availability.jsonl.gz','accuracy_updates.json','accuracy_reconstruction.json']})
    assert verification['source_hashes_still_match']
    (HERE/'accuracy_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    # Diagnostic ranking preserves the complete evaluation cohort.
    ranked=[]
    for identity in sorted({(r['episode'],r['query_decision'],r['pixel_index']) for r in rows}):
        query=[r for r in rows if (r['episode'],r['query_decision'],r['pixel_index'])==identity]
        errors=[r['world_error_m'] for r in query if r['reference_visible'] is True and r['accepted']]
        ranked.append(dict(episode=identity[0],query_decision=identity[1],pixel_index=identity[2],camera=query[0]['camera'],
            reference_body=query[0]['reference_body'],accepted_visible_count=len(errors),
            accepted_visible_over_3mm=sum(e>.003 for e in errors),max_visible_error_m=max(errors,default=None),
            occluded_accepted=sum(r['reference_visible'] is False and r['accepted'] for r in query)))
    ranked.sort(key=lambda x:(x['accepted_visible_over_3mm'],x['occluded_accepted']),reverse=True)
    (HERE/'accuracy_failure_cases.json').write_text(json.dumps(dict(scope='Diagnostic ranking; no query removed from gates.',queries=ranked),indent=2)+'\n')
    labels=['All endpoints','Fixed camera','Wrist camera','Translation','Rotation','Start 1','Start 2']
    stats=[result['overall'],result['groups']['camera']['agentview'],result['groups']['camera']['robot0_eye_in_hand'],
        result['groups']['motion_type']['translation'],result['groups']['motion_type']['rotation'],
        result['groups']['paired_state']['1'],result['groups']['paired_state']['2']]
    fig,axes=plt.subplots(1,3,figsize=(12,4.3),sharey=True,layout='constrained')
    y=np.arange(len(labels))
    specs=[('visible_coverage',100,'Accepted visible (%)',80),('accepted_error_p95_m',1000,'Accepted error p95 (mm)',3),
        ('occluded_false_valid_rate',100,'Accepted occluded (%)',5)]
    for ax,(field,scale,title,gate) in zip(axes,specs):
        vals=[s[field]*scale if s[field] is not None else 0 for s in stats]
        ax.barh(y,vals,color=['#325c80']*len(y));ax.axvline(gate,color='#b34b40',linestyle='--')
        ax.set_xlabel(title);ax.set_yticks(y,labels);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    fig.suptitle('CoTracker3 causal endpoints: observed traces, 212 original queries')
    fig.savefig(HERE/'accuracy_gates.png',dpi=180)
    fig.savefig(HERE/'accuracy_gates.svg')
    svg=HERE/'accuracy_gates.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    print(json.dumps(dict(verification=verification,overall=result['overall'],availability=result['availability']),indent=2))


if __name__=='__main__':
    main()
