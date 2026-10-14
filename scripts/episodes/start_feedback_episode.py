"""Start one frozen matched episode with identical processed robot sensing."""
import argparse,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
from fyp.feedback_runtime import SharedFeedbackEpisode
from fyp.episode import serve,write_json
p=argparse.ArgumentParser();p.add_argument('episode_id');p.add_argument('--protocol',type=Path,default=root/'studies/tool_hang_v2/protocol.json');p.add_argument('--port',type=int,default=8765);args=p.parse_args()
protocol=json.loads(args.protocol.read_text());trial=next(t for t in protocol['episodes'] if t['episode_id']==args.episode_id)
for path,expected in {**protocol['source_hashes'],**protocol['material_hashes']}.items():
 if not (root/path).exists() or hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:raise SystemExit('Frozen source/material missing or changed: '+path+'. Historical protocols require their recorded Git revision.')
current={str(f.relative_to(root)) for d in ['src','scripts'] for f in (root/d).rglob('*.py')}
assert current==set(protocol['source_hashes'])
episode=SharedFeedbackEpisode(root/'runs'/trial['episode_id'],task=protocol['task'],suite=protocol['suite'],seed=trial['seed'],state_index=trial['state_index'],
 condition=trial['condition'],calibration=protocol['calibration'],interrupt_empty=trial['condition']=='empty_closure_guard',
 **{k:protocol['shared'][k] for k in ['size','max_steps','max_calls','settle_steps']})
episode.config['frozen_study']=dict(study_id=protocol['study_id'],episode_id=trial['episode_id'],paired_state=trial['paired_state'],
 protocol_sha256=hashlib.sha256(args.protocol.read_bytes()).hexdigest(),source_hashes_verified=True,material_hashes=protocol['material_hashes'])
write_json(episode.folder/'config.json',episode.config);serve(episode,args.port)
