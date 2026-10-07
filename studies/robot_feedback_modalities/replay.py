"""Replay a fixed verification with the original sensor sampling phase."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from fyp.runtime import make_env,add_robot_sensors,proprio
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);args=p.parse_args()
folder=args.run.resolve();config=json.loads((folder/'config.json').read_text());saved=np.load(folder/'trajectory.npz')
rows=[json.loads(s) for s in (folder/'steps.jsonl').read_text().splitlines()]
env,obs,initial=make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
assert np.array_equal(initial,saved['initial'])
max_state=max_sensor=0.
for index,action in enumerate(saved['actions']):
    obs,_,_,_=env.step(action);add_robot_sensors(env,obs)
    max_state=max(max_state,float(np.max(np.abs(env.get_sim_state()-saved['states'][index]))))
    actual=proprio(obs)
    for key,expected in rows[index]['proprioception_after'].items():
        max_sensor=max(max_sensor,float(np.max(np.abs(np.asarray(actual[key])-expected))))
success=bool(env.check_success());env.close()
assert max_state==max_sensor==0.
assert success==json.loads((folder/'outcome.json').read_text())['success']
result=dict(all_pass=True,steps=len(rows),max_state_absolute_error=max_state,max_public_sensor_absolute_error=max_sensor,
    native_outcome_matches=True,actual_astra_requests=0,initialization='Original seeded initialization; no forced observable updates.',
    command=f'.venv/bin/python studies/robot_feedback_modalities/replay.py --run {folder}',
    replay_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    metadata_correction='Replaces the unsupported --replay-only command printed by the frozen calibration driver; source, actions, measurements and outcomes are unchanged.')
(folder/'replay_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
