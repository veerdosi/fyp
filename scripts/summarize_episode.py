"""Offline diagnostic measurements; never exposed to the robot policy."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def summarize(run):
    config = json.loads((run / 'config.json').read_text())
    steps = read_lines(run / 'steps.jsonl')
    events = read_lines(run / 'commands.jsonl')
    outcome_path = run / 'outcome.json'
    outcome = json.loads(outcome_path.read_text()) if outcome_path.exists() else None
    goals = {}
    for step in steps:
        for goal in step.get('diagnostic_goal_predicates', []):
            key = json.dumps(goal['predicate'], sort_keys=True)
            if goal['satisfied'] and key not in goals:
                goals[key] = step['step']
    commands = []
    for event in events:
        command = event['command']
        executed = [s for s in steps if s['command_id'] == event['call']]
        waypoints, cumulative = [], 0
        for wp in command.get('waypoints', []):
            start = cumulative
            cumulative += wp['steps']
            segment = executed[start:cumulative]
            row = {'target': wp, 'executed_steps': len(segment)}
            if segment:
                measurement = segment[-1]['proprioception_after']
                row['last_step'] = segment[-1]['step']
                row['measured_end_pose'] = {
                    k: measurement[k] for k in ['robot0_eef_pos', 'robot0_eef_quat']}
                row['terminal_position_error_m'] = float(np.linalg.norm(
                    np.asarray(wp['position']) - measurement['robot0_eef_pos']))
                q = wp.get('quaternion_xyzw', segment[0]['executor_measurement']['robot0_eef_quat'])
                row['terminal_orientation_error_rad'] = float((
                    Rotation.from_quat(q) * Rotation.from_quat(measurement['robot0_eef_quat']).inv()).magnitude())
                row['peak_raw_wrist_force_norm_N'] = float(max(
                    np.linalg.norm(s['proprioception_after']['robot0_eef_force']) for s in segment))
                row['last_finger_positions_m'] = measurement['robot0_gripper_qpos']
            waypoints.append(row)
        commands.append({'decision': event['call'], 'command': command,
                         'validation_error': event.get('result', {}).get('validation_error'),
                         'first_step': executed[0]['step'] if executed else None,
                         'last_step': executed[-1]['step'] if executed else None,
                         'waypoints': waypoints})
    first_success = next((s['step'] for s in steps if s['scoring_success']), None)
    policy_decisions = sum(bool(json.loads(p.read_text()).get('policy'))
                           for p in run.glob('policy_turn_*.json'))
    result = {'episode': run.name, 'task': config['task'], 'condition': config['condition'],
              'code_revision': config['code_revision'], 'outcome': outcome,
              'recorded_control_steps': len(steps), 'recorded_command_decisions': len(events),
              'policy_decisions': policy_decisions,
              'first_native_success_step': first_success,
              'first_satisfied_goal_steps': goals, 'commands': commands,
              'scope': 'Offline measurements, not automatic causal attribution. Raw wrist loads include gravity and dynamics.'}
    if all('execution_wall_seconds' in e for e in events) and 'setup_wall_seconds' in config:
        execution_seconds = sum(e['execution_wall_seconds'] for e in events)
        policy_seconds = sum(json.loads(p.read_text()).get('policy', {}).get('policy_wall_seconds') or 0
                             for p in run.glob('policy_turn_*.json'))
        elapsed = events[-1]['completed_wall_seconds'] if events else config['setup_wall_seconds']
        result['wall_time_components'] = {
            'setup_and_settling_seconds': config['setup_wall_seconds'],
            'command_execution_and_recording_seconds': execution_seconds,
            'policy_dispatch_to_delivered_response_seconds': policy_seconds,
            'elapsed_through_last_recorded_command_seconds': elapsed,
            'residual_operator_and_orchestration_seconds': elapsed-config['setup_wall_seconds']-execution_seconds-policy_seconds,
            'note': 'Dispatch-to-delivered-response includes message delivery delay. Native completed-turn duration is separately exported in policy_usage. Simulated control time is separate; residual is not model latency.'}
    usage_path = run / 'policy_usage.json'
    if usage_path.exists():
        result['policy_usage'] = json.loads(usage_path.read_text())
        if 'wall_time_components' in result:
            native = result['policy_usage']['policy_wall_seconds']
            result['wall_time_components']['native_completed_policy_turn_seconds'] = native
            result['wall_time_components']['delivered_response_minus_native_turn_seconds'] = policy_seconds-native
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    result = summarize(args.run)
    destination = args.run / 'diagnostic_summary.json'
    destination.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({k: v for k, v in result.items() if k not in ['commands', 'policy_usage']}, indent=2))
