"""Record an episode policy's temporary sensor calculation and its outputs.

This is a logging wrapper, not a filesystem or network sandbox. Sensor and
repository restrictions are enforced through instructions and trace audit.
It cannot submit a robot command or access a simulator through its interface.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--run', required=True)
parser.add_argument('--code', required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
run=Path(args.run).resolve()
work=run/'policy_compute'
work.mkdir(exist_ok=True)
code=Path(args.code).resolve()
if not code.is_relative_to(work) or code.suffix!='.py':
    raise SystemExit('Code must be a .py file inside this episode\'s policy_compute directory')
obs=json.loads((run/'public/latest.json').read_text())
archive=run/'policy_calculation_logs'
archive.mkdir(exist_ok=True)
n=len(list(archive.glob('calc_*')))+1
record=archive/f'calc_{n:03d}'
record.mkdir()
source=code.read_bytes()
(record/'code.py').write_bytes(source)
t0=time.monotonic()
environment={'PATH':str(root/'.venv/bin')+':/usr/bin:/bin:/usr/sbin:/sbin',
             'PYTHONNOUSERSITE':'1','OPENBLAS_NUM_THREADS':'1',
             'POLICY_OBSERVATION_FOLDER':obs['folder'],
             'POLICY_PUBLIC_FOLDER':str(run/'public'),
             'POLICY_COMPUTE_FOLDER':str(work)}
try:
    result=subprocess.run([str(root/'.venv/bin/python'),'-B',str(record/'code.py')],
                          cwd=work, env=environment, capture_output=True, timeout=30)
    stdout,stderr=result.stdout,result.stderr
    returncode=result.returncode
    stop='completed'
except subprocess.TimeoutExpired as exc:
    stdout,stderr=exc.stdout or b'',exc.stderr or b''
    returncode=None
    stop='timeout'
(record/'stdout.txt').write_bytes(stdout)
(record/'stderr.txt').write_bytes(stderr)
metadata=dict(observation_id=obs['observation_id'],step=obs['step'],
              source_file=str(code),source_sha256=hashlib.sha256(source).hexdigest(),
              returncode=returncode,stop_reason=stop,wall_seconds=time.monotonic()-t0,
              sensor_manifest={str(p.relative_to(run/'public')):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((run/'public').rglob('*')) if p.is_file()},
              note='Policy sensor calculation; instruction/audit boundary, no filesystem sandbox')
(record/'metadata.json').write_text(json.dumps(metadata,indent=2))
print(stdout.decode(errors='replace'),end='')
if stderr:
    print(stderr.decode(errors='replace'),end='')
print('\nCalculation record:',record)
if returncode not in [0,None]:
    raise SystemExit(returncode)
