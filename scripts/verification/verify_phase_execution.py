"""Recorded simulator verification and pilot-duration diagnostic; no model calls.

This reuses Astra-authored pilot targets and public robot measurements. It never
constructs a grasp, reads object truth to select motion, or attempts a new task plan.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'src'))
from fyp.episode import Episode, write_json


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--condition', choices=['direct_waypoints', 'deadline_guard', 'phase_guard'],
                    default='direct_waypoints')
parser.add_argument('--duration-scale', type=int, choices=[1, 2], default=1)
parser.add_argument('--hold-check', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
source = root/'runs/pilot_tool_hang_002/policy_turn_002.json'
points = copy.deepcopy(json.loads(source.read_text())['command']['waypoints'])
ep = Episode(args.run, suite='robosuite', task='ToolHang', seed=401,
             state_index=1, condition=args.condition)
ep.config.update(model=None, reasoning_effort=None, verification_only=True,
                 diagnostic_source=str(source.relative_to(root)),
                 diagnostic_duration_scale=args.duration_scale,
                 diagnostic_hold_check=args.hold_check,
                 reproduce_command=' '.join([str(root/'.venv/bin/python'), str(Path(__file__).resolve()),
                     '--run NEW_UNUSED_FOLDER --condition', args.condition,
                     '--duration-scale', str(args.duration_scale),
                     '--hold-check' if args.hold_check else '']).strip())
write_json(ep.folder/'config.json', ep.config)
results = []
if args.hold_check:
    sensors = ep.latest['proprioception']
    hold = dict(position=sensors['robot0_eef_pos'],
                quaternion_xyzw=sensors['robot0_eef_quat'], gripper=-1, steps=40)
    results.append(ep.command({'command':dict(type='move', waypoints=[hold]),
                               'operator_verification':'Hold an already-measured robot pose.'}))
if args.duration_scale == 1:
    results.append(ep.command({'command':dict(type='move', waypoints=points),
                               'operator_verification':'Exact Astra-authored pilot sequence.'}))
else:
    # Split at the existing per-command bound; no intervening policy choices.
    for point in points:
        point['steps'] *= args.duration_scale
        results.append(ep.command({'command':dict(type='move', waypoints=[point]),
                                   'operator_verification':'Double recorded durations; targets and order unchanged.'}))
results.append(ep.command({'command':dict(type='finish', reason='Operator diagnostic complete'),
                           'operator_verification':'Not a policy completion claim.'}))
ep.events.close()
write_json(ep.folder/'operator_verification.json', dict(
    policy_inference_requests=0, source=str(source.relative_to(root)),
    duration_scale=args.duration_scale, hold_check=args.hold_check,
    results=results,
    scope='Execution/duration diagnostic only; native partial progress is private diagnosis, not a task-success comparison.'))
if args.hold_check:
    first = results[0]['execution_report']['waypoints'][0]
    sequence = results[1]['execution_report']
    if args.condition == 'phase_guard':
        assert first['status'] == 'arrived' and first['executed_steps'] < 40
    elif args.condition == 'deadline_guard':
        assert first['status'] == 'arrived' and first['executed_steps'] == 40
    else:
        assert first['executed_steps'] == 40
    if args.condition != 'direct_waypoints':
        assert sequence['stop_reason'] == 'waypoint_deadline'
        assert sequence['remaining_waypoints_cancelled'] == 3
        assert len(sequence['waypoints']) == 1
    else:
        assert len(sequence['waypoints']) == 4
    write_json(ep.folder/'implementation_checks.json', dict(
        passed=True, checks=['measured hold duration', 'deadline cancellation versus timed advancement'],
        scope='Actual simulator commands; assertions are about execution semantics, not task competence.'))
print((ep.folder/'outcome.json').read_text())
