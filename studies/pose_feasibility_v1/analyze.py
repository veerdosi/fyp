"""Descriptive corrected-pair account; incomplete evidence remains explicit."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from analyze_study import wilson


def load(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def normalize(text, run):
    return text.replace(str(run.resolve()), '<RUN>').replace(run.name, '<EPISODE>')


def matched_inputs(a, b):
    assert np.array_equal(np.load(a / 'initial_state.npy'), np.load(b / 'initial_state.npy'))
    relative = ['public/obs_0000/' + name for name in [
        'observation.json', 'calibration.json', 'sensor_feedback.json',
        'sensor_feedback_samples.jsonl', 'agentview.png', 'agentview_depth_m.npy',
        'robot0_eye_in_hand.png', 'robot0_eye_in_hand_depth_m.npy']]
    relative += ['public/robot_kinematics/' + name for name in [
        'robot.xml', 'parameters.json', 'kinematic_preview.py']]
    relative += ['public/feedback_calibration.json']
    checked = []
    for name in relative:
        left, right = a / name, b / name
        if left.suffix in ['.json', '.jsonl']:
            assert normalize(left.read_text(), a) == normalize(right.read_text(), b), name
        else:
            assert left.read_bytes() == right.read_bytes(), name
        checked.append(name)
    common = []
    for run in [a, b]:
        text = (run / 'policy_initial.txt').read_text()
        capability = (run / 'policy_condition_capability.txt').read_text()
        assert capability in text
        common.append(normalize(text.replace(capability, '<CONDITION_CAPABILITY>'), run))
    assert common[0] == common[1]
    return dict(initial_state_exact=True, public_files_exact_after_path_normalization=checked,
                prepared_common_prompt_exact=True,
                normalized_common_prompt_sha256=hashlib.sha256(common[0].encode()).hexdigest(),
                dispatch_scope='Saved text manually copied verbatim; encrypted native initial archive prevents independent automated plaintext equality.')


def episode(trial, protocol):
    run = ROOT / 'runs' / trial['episode_id']
    row = dict(trial, status='missing', success=None)
    if not (run / 'outcome.json').exists():
        row['status'] = 'running' if run.exists() else 'missing'
        return row
    config, outcome = load(run / 'config.json'), load(run / 'outcome.json')
    assert config['source_hashes'] == protocol['source_hashes']
    assert config['model'] == protocol['model'] and config['reasoning_effort'] == protocol['reasoning_effort']
    for key in ['seed', 'state_index', 'condition']:
        assert config[key] == trial[key], key
    for key, value in protocol['shared'].items():
        assert config[key] == value, key
    assert config['sensor_feedback']['calibration'] == protocol['calibration']
    assert config['sensor_feedback']['interrupt_empty'] == protocol['common_empty_interrupt']
    assert config['pose_preview']['parameters'] == protocol['solver_parameters']
    assert config['pose_preview']['enabled'] == (trial['condition'] == 'pose_preview')
    events = lines(run / 'commands.jsonl')
    waypoints = [wp for event in events for wp in event.get('result', {}).get('execution_report', {}).get('waypoints', [])]
    queries = [event for event in events if event['command']['type'] == 'preview']
    candidates = [pose for event in queries for pose in event.get('result', {}).get('poses', [])]
    exits = [wp['terminal_measurement'] for wp in waypoints if wp.get('terminal_measurement')]
    nonarrivals = sum(m['position_error_m'] > .003 or m['orientation_error_rad'] > .03 for m in exits)
    row.update(status='recorded', success=outcome['success'], stop_reason=outcome['stop_reason'],
               decisions=outcome['model_calls'], simulated_seconds=outcome['simulated_seconds'],
               host_wall_seconds=outcome['wall_seconds'], source_revision=config['code_revision'],
               recorded_protocol_sha256=config['frozen_study']['protocol_sha256'],
               native_terminal_checks=outcome['diagnostic_goal_predicates'],
               executed_waypoint_exits=len(exits), nonarriving_waypoint_exits=nonarrivals,
               waypoint_exit_status_counts={status: sum(wp['status'] == status for wp in waypoints)
                   for status in sorted({wp['status'] for wp in waypoints})},
               nonarrival_fraction=nonarrivals / len(exits) if exits else None,
               preview_decisions=len(queries), preview_candidates=len(candidates),
               bounded_solutions_found=sum(p['best']['solution_found'] for p in candidates),
               preview_solver_seconds=sum(p['seconds'] for p in candidates),
               command_execution_seconds=sum(e['execution_wall_seconds'] for e in events))
    for name in ['policy_usage', 'replay_verification', 'diagnostic_summary', 'causal_review', 'policy_tool_audit']:
        row[name] = load(run / (name + '.json')) if (run / (name + '.json')).exists() else None
    usage = row['policy_usage']
    if usage:
        row.update(inference_requests=usage['model_inference_requests'],
                   native_policy_seconds=usage['policy_wall_seconds'],
                   api_equivalent_cost_usd=usage['api_equivalent_standard_cost_usd'])
    row['complete_evidence'] = bool(usage and row['replay_verification'] and row['replay_verification']['all_pass']
        and row['diagnostic_summary'] and row['causal_review'] and row['policy_tool_audit']
        and row['policy_tool_audit'].get('tool_boundary_pass'))
    return row


protocol = load(HERE / 'protocol.json')
rows = [episode(trial, protocol) for trial in protocol['episodes']]
pairs = []
for state in range(1, protocol['paired_state_count'] + 1):
    subset = [r for r in rows if r['paired_state'] == state]
    if not all(r['status'] == 'recorded' for r in subset):
        continue
    baseline = next(r for r in subset if r['condition'] == 'direct_waypoints_encoder')
    preview = next(r for r in subset if r['condition'] == 'pose_preview')
    pair = dict(paired_state=state, baseline=baseline['episode_id'], preview=preview['episode_id'],
                inputs=matched_inputs(ROOT / 'runs' / baseline['episode_id'], ROOT / 'runs' / preview['episode_id']),
                both_succeeded=baseline['success'] and preview['success'],
                success_difference=int(preview['success']) - int(baseline['success']))
    for metric in ['decisions', 'inference_requests', 'simulated_seconds', 'native_policy_seconds', 'api_equivalent_cost_usd']:
        if metric in baseline and metric in preview:
            pair[metric + '_difference_preview_minus_baseline'] = preview[metric] - baseline[metric]
            if pair['both_succeeded']:
                pair[metric + '_ratio_preview_over_baseline'] = preview[metric] / baseline[metric] if baseline[metric] else None
    pairs.append(pair)
summaries = {}
for condition in ['direct_waypoints_encoder', 'pose_preview']:
    completed = [r for r in rows if r['condition'] == condition and r['status'] == 'recorded']
    wins = sum(r['success'] for r in completed)
    summaries[condition] = dict(scheduled=2, completed=len(completed), successes=wins,
        success_rate=wins / len(completed) if completed else None,
        descriptive_wilson_95=wilson(wins, len(completed)))
result = dict(study_id=protocol['study_id'], trials=rows, paired_results=pairs, condition_summaries=summaries,
    complete=all(r.get('complete_evidence', False) for r in rows) and len(pairs) == 2,
    corrected_schedule='Amendment 002: four corrected episodes on two states; removed episode excluded entirely.',
    statistical_scope='Two descriptive pairs; wide uncertainty, no general reliability or significance claim. Both pairs execute preview before baseline.',
    resource_scope='Completion ratios only for jointly successful pairs. Host elapsed includes orchestration/pauses; native policy and local execution clocks are separate.',
    solver_scope='Bounded geometric search; neither global reachability nor contact, dynamic arrival or object-relation certificate.')
(HERE / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['trials', 'paired_results']}, indent=2))
