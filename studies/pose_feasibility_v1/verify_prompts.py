"""Compare actual saved zero-decision handoffs on identical known fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from fyp.pose_preview import PosePreviewEpisode

calibration=json.loads((ROOT/'studies/tool_hang_v2/protocol.json').read_text())['calibration']
parameters=json.loads((HERE/'solver_parameters.json').read_text())
common=[]
initial=[]
for enabled in [False,True]:
    folder=HERE/('prompt_fixture_preview' if enabled else 'prompt_fixture_waypoints')
    e=PosePreviewEpisode(folder,task='ToolHang',suite='robosuite',seed=601,state_index=31,
        condition='fixed_sequence',size=256,max_steps=2400,max_calls=30,settle_steps=20,
        calibration=calibration,interrupt_empty=True,preview_enabled=enabled,solver_parameters=parameters)
    done=subprocess.run([sys.executable,str(ROOT/'scripts/prepare_pose_preview_policy.py'),str(folder)],
                        capture_output=True,text=True)
    (folder/'preparation_stdout.log').write_text(done.stdout)
    (folder/'preparation_stderr.log').write_text(done.stderr)
    assert done.returncode==0,done.stderr
    message=(folder/'policy_initial.txt').read_text()
    capability=(folder/'policy_condition_capability.txt').read_text()
    assert capability in message
    normalized=message.replace(capability,'<CONDITION_CAPABILITY>').replace(str(folder.resolve()),'<RUN>').replace(folder.name,'<EPISODE>')
    assert 'do not import fyp, libero or robosuite' in normalized
    assert 'mujoco solely to compile' in normalized
    assert 'an armed empty-sized closure interrupts' in normalized
    common.append(normalized)
    initial.append(e.env.get_sim_state().copy())
    e.finish('fixed_prompt_verification');e.events.close()
assert common[0]==common[1]
assert np.array_equal(initial[0],initial[1])
result=dict(common_policy_text_exact_after_paths_and_declared_capability_normalized=True,
    initial_states_exact=True,actual_astra_requests=0,
    normalized_common_sha256=hashlib.sha256(common[0].encode()).hexdigest(),
    reproduce='.venv/bin/python studies/pose_feasibility_v1/verify_prompts.py (fresh fixture folders required)')
(HERE/'prompt_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
