"""Start one episode from the frozen pose-feasibility experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.pose_preview import PosePreviewEpisode
from fyp.episode import serve,write_json

p=argparse.ArgumentParser()
p.add_argument('episode_id')
p.add_argument('--port',type=int,default=8765)
args=p.parse_args()
path=ROOT/'studies/pose_feasibility_v1/protocol.json'
protocol=json.loads(path.read_text())
for relative,expected in {**protocol['source_hashes'],**protocol['material_hashes']}.items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
actual={str(f.relative_to(ROOT)) for d in ['src','scripts'] for f in (ROOT/d).rglob('*.py')}
assert actual==set(protocol['source_hashes'])
trial=next(x for x in protocol['episodes'] if x['episode_id']==args.episode_id)
episode=PosePreviewEpisode(ROOT/'runs'/args.episode_id,task=protocol['task'],suite=protocol['suite'],
    seed=trial['seed'],state_index=trial['state_index'],condition=trial['condition'],
    calibration=protocol['calibration'],interrupt_empty=True,preview_enabled=trial['condition']=='pose_preview',
    solver_parameters=protocol['solver_parameters'],**protocol['shared'])
episode.config['frozen_study']=dict(study_id=protocol['study_id'],paired_state=trial['paired_state'],
    protocol_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_hashes_verified=True)
write_json(episode.folder/'config.json',episode.config)
serve(episode,args.port)
