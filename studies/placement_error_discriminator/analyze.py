"""Offline placement diagnosis from all five calculations in the completed batch."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text())


def relative(row, name):
    robot = row['proprioception_after']
    obj = row['diagnostic_object_observations']
    rotation = Rotation.from_quat(robot['robot0_eef_quat'])
    position = rotation.inv().apply(np.asarray(obj[name + '_pos']) - robot['robot0_eef_pos'])
    orientation = rotation.inv() * Rotation.from_quat(obj[name + '_quat'])
    # Verify quaternion convention and frame against the pinned native observable.
    assert np.max(np.abs(position - obj[name + '_to_robot0_eef_pos'])) < 1e-6
    assert (orientation * Rotation.from_quat(obj[name + '_to_robot0_eef_quat']).inv()).magnitude() < 1e-6
    return position, orientation


def main():
    protocol = load(ROOT / 'studies/pose_feasibility_v1/protocol.json')
    evidence = []
    for trial in protocol['episodes']:
        run = ROOT / 'runs' / trial['episode_id']
        steps = [json.loads(line) for line in (run / 'steps.jsonl').read_text().splitlines()]
        events = [json.loads(line) for line in (run / 'commands.jsonl').read_text().splitlines()]
        for calc in sorted((run / 'policy_calculation_logs').glob('calc_*')):
            metadata = load(calc / 'metadata.json')
            code = calc / 'code.py'
            assert hashlib.sha256(code.read_bytes()).hexdigest() == metadata['source_sha256']
            # Sources were individually reviewed: pure literal NumPy/SciPy arithmetic,
            # no file/network/simulator access or mutation. Reproduce outside policy.
            result = subprocess.run([sys.executable, str(code)], capture_output=True, text=True, check=True)
            assert result.stdout == (calc / 'stdout.txt').read_text()
            assert result.stderr == (calc / 'stderr.txt').read_text()
            following = next(event for event in events if event['command']['type'] == 'move'
                             and any(s['command_id'] == event['call'] and s['step'] > metadata['step'] for s in steps))
            segment = [s for s in steps if s['command_id'] == following['call']]
            reference = next(s for s in steps if s['step'] == metadata['step'])
            obj = 'tool' if 'tool' in metadata['source_file'] or 'hook_align' in metadata['source_file'] else 'frame'
            p0, q0 = relative(reference, obj)
            changes = []
            for row in segment:
                p, q = relative(row, obj)
                changes.append(dict(step=row['step'], position_change_m=float(np.linalg.norm(p-p0)),
                                    orientation_change_rad=float((q*q0.inv()).magnitude())))
            exits = following['result']['execution_report']['waypoints']
            evidence.append(dict(episode=run.name, calculation=calc.name, object_reference=obj,
                calculation_step=metadata['step'], following_decision=following['call'],
                first_step=segment[0]['step'], last_step=segment[-1]['step'], arithmetic_stdout_stderr_exact=True,
                source_sha256=metadata['source_sha256'],
                maximum_relative_position_change_m=max(c['position_change_m'] for c in changes),
                maximum_relative_orientation_change_rad=max(c['orientation_change_rad'] for c in changes),
                first_change=changes[0], last_change=changes[-1], samples=changes,
                first_position_change_above_reference_step=next((c['step'] for c in changes if c['position_change_m']>.003),None),
                first_orientation_change_above_reference_step=next((c['step'] for c in changes if c['orientation_change_rad']>.03),None),
                waypoint_exits=exits,
                policy_reason=following['command']['reason']))
    assert len(evidence) == 5, 'All five preregistered calculations must be retained'
    report = dict(preregistered_decision='studies/pose_feasibility_v1/next_test.md',
        all_five_calculations_retained=True, arithmetic_reproduced_exact=True,
        relative_frame_convention_verified=True, actual_astra_requests=0,
        scope='Private geometry is offline diagnosis only. Relative drift is measured, not a grasp certificate. Reference thresholds are descriptive, not new success gates. Surface identity and unrecorded intended offsets remain unknown.',
        calculations=evidence,
        command='.venv/bin/python studies/placement_error_discriminator/analyze.py',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ['samples','waypoint_exits','policy_reason']}
                      for row in evidence], indent=2))


if __name__ == '__main__':
    main()
