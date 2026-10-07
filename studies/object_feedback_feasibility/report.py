"""Check cohort completeness and plot the frozen measurement gates."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
cohort = json.loads((HERE/'cohort.json').read_text())
result = json.loads((HERE/'results.json').read_text())
reconstruction = json.loads((HERE/'sensor_reconstruction.json').read_text())
with gzip.open(HERE/'samples.jsonl.gz','rt') as f:
    rows = [json.loads(line) for line in f]
expected = {(s['episode'],p['query_decision'],p['pixel_index']):s['end_step']-s['start_step']
            for s in cohort['streams'] for p in s['points']}
counts = Counter((r['episode'],r['query_decision'],r['pixel_index']) for r in rows)
assert dict(counts) == expected, 'Missing or repeated query samples'
assert len(result['initial_queries']) == cohort['retained_query_count']
assert reconstruction['all_pass'] and reconstruction['bit_exact_images']
assert len(reconstruction['replay_checks']) == len(cohort['episodes'])
assert all(r['max_state_absolute_error']==0 for r in reconstruction['replay_checks'])
parameters = json.loads((HERE/'parameters.json').read_text())
for key, file in [('tracker_sha256','tracker.py'),('audit_driver_sha256','audit.py'),
                  ('camera_reference_sha256','camera_reference.py')]:
    assert hashlib.sha256((HERE/file).read_bytes()).hexdigest() == parameters[key]
assert result['parameters'] == parameters
verification = dict(pass_checks=True,queries=cohort['query_count'],
    scored_queries=len(expected),skipped_queries=cohort['skipped_queries'],
    expected_samples=sum(expected.values()),actual_samples=len(rows),
    replayed_steps=sum(c['steps'] for c in reconstruction['replay_checks']),
    exact_camera_snapshots=len(reconstruction['checks']),
    results_sha256=hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest(),
    samples_sha256=hashlib.sha256((HERE/'samples.jsonl.gz').read_bytes()).hexdigest(),
    actual_model_inference_requests=0,
    scope='Completeness and source verification, not statistical independence or task-success evidence.')
(HERE/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')

query_rows = defaultdict(list)
for row in rows:
    key = (row['episode'],row['query_decision'],row['pixel_index'],row['reference_body'],row['camera'])
    query_rows[key].append(row)
cases = []
for key, samples in query_rows.items():
    bad = [r for r in samples if r['accepted'] and r['reference_visible'] is True and r['world_error_m']>.003]
    false_valid = [r for r in samples if r['accepted'] and r['reference_visible'] is False]
    if bad or false_valid:
        cases.append(dict(key=key,bad_visible=len(bad),false_valid=len(false_valid),total=len(samples),
            first_bad=bad[0]['step'] if bad else None,first_false=false_valid[0]['step'] if false_valid else None,
            max_error_m=max((r['world_error_m'] for r in bad),default=None),
            bad_forward_backward_median_pixels=float(np.median([r['forward_backward_pixels'] for r in bad])) if bad else None))
cases.sort(key=lambda c:c['bad_visible']+c['false_valid'],reverse=True)
(HERE/'failure_cases.json').write_text(json.dumps(dict(
    selection='Diagnostic ranking by accepted errors above 3mm plus accepted reference-occluded samples. Full cohort retained; these are not evaluation subsets.',
    loss_sample_counts=dict(Counter(r['loss_reason'] for r in rows if not r['accepted'])),cases=cases),indent=2)+'\n')

groups = [('camera','agentview','Fixed camera'),('camera','robot0_eye_in_hand','Wrist camera'),
          ('motion_type','translation','Translation'),('motion_type','rotation','Includes rotation'),
          ('paired_state','1','Start 1'),('paired_state','2','Start 2')]
labels = [g[2] for g in groups]
stats = [result['groups'][key][value] for key,value,_ in groups]
fig, axes = plt.subplots(1,3,figsize=(11,4.8),sharey=True,layout='constrained')
settings = [('visible_coverage',100,80,'Accepted visible samples (%)'),
            ('accepted_error_p95_m',1000,3,'Accepted current-point error, p95 (mm)'),
            ('occluded_false_valid_rate',100,5,'Accepted occluded samples (%)')]
for ax,(key,scale,gate,title) in zip(axes,settings):
    values = [s[key]*scale if s[key] is not None else np.nan for s in stats]
    ax.barh(np.arange(len(stats)),values,color='#406e8e',height=.65)
    ax.axvline(gate,color='#b54242',linestyle='--',linewidth=1.4,label='Frozen gate')
    ax.set_xlabel(title)
    ax.grid(axis='x',alpha=.2)
    if scale == 100:
        ax.set_xlim(0,100)
    else:
        ax.set_xlim(0,max([gate]+[v for v in values if np.isfinite(v)])*1.25)
    for index,value in enumerate(values):
        if np.isfinite(value):
            ax.annotate(f'{value:.1f}',(value,index),xytext=(4,0),textcoords='offset points',va='center',fontsize=8)
        else:
            ax.text(0,index,'No reference samples',va='center',fontsize=8)
axes[0].set_yticks(np.arange(len(labels)),labels)
axes[0].invert_yaxis()
fig.suptitle('RGB-D point measurement on recorded ToolHang motions',fontsize=13)
fig.supxlabel('Development audit; correlated frames and points, zero new policy episodes',fontsize=9)
fig.savefig(HERE/'measurement_gates.png',dpi=160)
fig.savefig(HERE/'measurement_gates.svg')
print(json.dumps(verification,indent=2))
