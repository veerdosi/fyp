"""Verify complete frozen screens and report the limits of each feedback signal."""
import gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
result=json.loads((HERE/'monitor_result.json').read_text())
protocol=json.loads((HERE/'monitor_protocol.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in protocol['source_hashes'].items())
read=lambda name:[json.loads(x) for x in gzip.open(HERE/name,'rt')]
rows=read('monitor_samples.jsonl.gz');contacts=read('private_contact_context.jsonl.gz');context={(r['episode'],r['step']):r for r in contacts}
assert len(context)==len(contacts)==10878
assert len({(r['episode'],r['step']) for r in rows})==len(rows)==result['samples']
trials=json.loads((ROOT/'studies/tool_hang_v1/protocol.json').read_text())['episodes']
expected=set()
for t in trials+protocol['calibration_trials']:
 folder=ROOT/t['folder'] if 'folder' in t else ROOT/'runs'/t['episode_id']
 for r in [json.loads(x) for x in (folder/'steps.jsonl').read_text().splitlines()]:
  if r['waypoint_index'] is not None:expected.add((folder.name,r['step']))
assert expected=={(r['episode'],r['step']) for r in rows}
empty=[];loads=[];stalls=[]
for w in result['waypoints']:
 if w['calibration']:continue
 for kind,target in [('empty_sized_closure',empty),('load_change',loads),('stalled_motion',stalls)]:
  step=w['first_flags'][kind]
  if step is None:continue
  c=context[(w['episode'],step)]
  target.append(dict(episode=w['episode'],command_id=w['command_id'],waypoint_index=w['waypoint_index'],first_flag_step=step,
   original_waypoint_end=w['last_step'],remaining_original_waypoint_steps=w['last_step']-step,
   private_both_pad_objects=c['both_pad_objects'],private_gripper_contacts=sum(x['gripper'] for x in c['contacts']),
   private_proximal_contacts=sum(not x['gripper'] for x in c['contacts'])))
phase=[r for r in rows if r['episode']=='th_v1_s01_phase_guard' and r['command_id']==16]
loss=[r for r in contacts if r['episode']=='th_v1_s01_phase_guard' and 1180<=r['step']<=1379 and any(not p['satisfied'] for p in r['native_goal_predicates'] if p['predicate']==['frame_assembled'])]
summary=dict(scope='Observed-trace sensor diagnostics; no causal prevention or task-success claim.',complete=True,
 monitor_rows=len(rows),private_geometry_rows=len(contacts),waypoints=len(result['waypoints']),by_scope=result['by_scope'],
 empty_closure_events=empty,load_events=loads,stall_events=stalls,
 empty_flags_without_two_pad_frame_tool_stand_contact=sum(not e['private_both_pad_objects'] for e in empty),
 load_first_flags_without_gripper_contact=sum(e['private_gripper_contacts']==0 for e in loads),
 load_first_flags_without_any_robot_environment_contact=sum(e['private_gripper_contacts']==e['private_proximal_contacts']==0 for e in loads),
 phase_withdrawal=dict(first_frame_check_failure=loss[0]['step'] if loss else None,
  proximal_contact_steps=sum(any(not c['gripper'] for c in r['contacts']) for r in loss),
  load_flag_steps=[r['step'] for r in phase if r['flags']['load_change']],
  stall_flag_steps=[r['step'] for r in phase if r['flags']['stalled_motion']],
  limitation='An upstream arm-frame collision is not reliably sensed by a downstream wrist force sensor.'))
(HERE/'screen_account_data.json').write_text(json.dumps(summary,indent=2)+'\n')
verification=dict(all_pass=True,all_frozen_sources_match=True,all_expected_monitor_frames_retained=True,
 private_geometry_rows=len(contacts),actual_astra_requests=0,
 files_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['monitor_samples.jsonl.gz','private_contact_context.jsonl.gz','monitor_result.json','screen_account_data.json']})
(HERE/'monitor_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['monitor_rows','private_geometry_rows','empty_flags_without_two_pad_frame_tool_stand_contact','load_first_flags_without_gripper_contact','load_first_flags_without_any_robot_environment_contact','phase_withdrawal']},indent=2))
