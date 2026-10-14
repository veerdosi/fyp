"""Start one frozen study episode after checking the recorded source hashes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root/'src'))
from fyp.episode import Episode, serve, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('episode_id')
parser.add_argument('--protocol', type=Path, default=root/'studies/tool_hang_v1/protocol.json')
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
protocol = json.loads(args.protocol.read_text())
trial = next(t for t in protocol['episodes'] if t['episode_id'] == args.episode_id)
for relative, expected in protocol['source_hashes'].items():
    if not (root/relative).exists() or hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Frozen source missing/changed: {relative}. Historical protocols require their recorded Git revision.')
for relative, expected in protocol['material_hashes'].items():
    if not (root/relative).exists() or hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Frozen policy/dependency material changed: {relative}')
current = {str(p.relative_to(root)) for folder in ['src','scripts']
           for p in (root/folder).rglob('*.py')}
if current != set(protocol['source_hashes']):
    raise SystemExit('Frozen Python source inventory changed')
ep = Episode(root/'runs'/trial['episode_id'], task=protocol['task'], suite=protocol['suite'],
             seed=trial['seed'], state_index=trial['state_index'], condition=trial['condition'],
             **{k:protocol['shared'][k] for k in ['size','max_calls','max_steps','settle_steps']})
assert ep.config['execution_criteria'] == protocol['arrival_criteria']
assert ep.config['versions'] == protocol['runtime_versions']
ep.config['frozen_study'] = dict(study_id=protocol['study_id'], episode_id=args.episode_id,
                               protocol_sha256=hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
                               paired_state=trial['paired_state'], source_hashes_verified=True,
                               material_hashes=protocol['material_hashes'])
write_json(ep.folder/'config.json', ep.config)
serve(ep, args.port)
