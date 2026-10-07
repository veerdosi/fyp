"""End-to-end check that the two conditions expose identical processed sensing."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'src'))
from fyp.feedback_runtime import SharedFeedbackEpisode
p=json.loads((HERE/'public_verification_protocol.json').read_text())
for path,expected in p['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
source=ROOT/'runs/th_v1_s01_direct_waypoints';config=json.loads((source/'config.json').read_text());saved=np.load(source/'trajectory.npz')
events={r['call']:r for r in [json.loads(s) for s in (source/'commands.jsonl').read_text().splitlines()]}
initials=[];publics=[];records=[]
for interrupt in [False,True]:
 folder=HERE/('public_guard' if interrupt else 'public_shadow')
 ep=SharedFeedbackEpisode(folder,task=config['task'],suite=config['suite'],seed=config['seed'],state_index=config['state_index'],
   condition='fixed_sequence',size=256,max_calls=10,max_steps=600,settle_steps=20,calibration=p['calibration'],interrupt_empty=interrupt)
 initials.append(np.asarray(ep.initial))
 for call in [2,3]:
  command=copy.deepcopy(events[call]['command'])
  for index,wp in enumerate(command['waypoints']):wp['abort_if_empty_close']=call==3 and index in [1,2]
  ep.command(dict(command=command))
 ep.finish('fixed_public_feedback_verification');ep.events.close()
 trajectory=np.load(folder/'trajectory.npz');assert np.array_equal(trajectory['actions'],saved['actions'][:335]);assert np.array_equal(trajectory['states'],saved['states'][:335])
 frames=[]
 for obs in sorted((folder/'public').glob('obs_*')):
  r=json.loads((obs/'sensor_feedback.json').read_text());r.pop('calibration_file');r.pop('samples_file');frames.append(r)
  assert json.loads((obs/'observation.json').read_text())['feedback_file']==str(obs/'sensor_feedback.json')
  if r['last_motion_summary']:assert (obs/'sensor_feedback_samples.jsonl').stat().st_size>0
 publics.append(frames);records.append(dict(folder=str(folder),steps=335,prefix_actions_states_exact=True,public_feedback_files=3,actual_astra_requests=0))
assert np.array_equal(initials[0],initials[1]);assert publics[0]==publics[1]
(HERE/'public_verification_result.json').write_text(json.dumps(dict(all_pass=True,initial_states_equal=True,processed_feedback_equal=True,records=records,
 actual_astra_requests=0,scope='Observed-state fixed publication verification, not a task-policy comparison.'),indent=2)+'\n')
print('Public feedback and action/state prefixes match in both conditions.',flush=True)
