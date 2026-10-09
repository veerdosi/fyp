"""Private native geometry diagnosis; never exposed to policy or executor."""
import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from fyp.runtime import make_env
from robosuite.utils.sim_utils import check_contact

source = ROOT / 'studies/tool_hang_v1/scorer_audit/audit.py'
# Reuse the already-verified native-check decomposition without running that
# module's v1 batch or changing its historical report.
node = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'inspect')
scope = dict(np=np, json=json, make_env=make_env, check_contact=check_contact)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
samples = []
for trial in json.loads((HERE / 'protocol.json').read_text())['episodes']:
    run = ROOT / 'runs' / trial['episode_id']
    if (run / 'outcome.json').exists():
        result = scope['inspect'](run)
        (run / 'native_terminal_geometry.json').write_text(json.dumps(result, indent=2) + '\n')
        samples.append(result)
report = dict(scope='Private terminal saved-state decomposition, not sensor evidence or new policy outcome.',
              samples=samples, original_decomposition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              reproduce='.venv/bin/python studies/pose_feasibility_v1/native_diagnosis.py',
              limitation='Rebuilt geometry contacts do not reconstruct contact forces. Native release '
              'checks cover fingerpads, not all robot links. Only the four corrected scheduled episodes are included.')
(HERE / 'native_terminal_geometry.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(samples, indent=2))
