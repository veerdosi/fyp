"""Describe every scheduled outcome; distinguish the unmatched first prompt."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from initial_match import verify as verify_initial

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def interval(wins, count):
    if not count:
        return None
    z = 1.959963984540054
    p = wins / count
    d = 1 + z * z / count
    c = (p + z * z / (2 * count)) / d
    h = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / d
    return [max(0, c - h), min(1, c + h)]


def analyze():
    protocol = read(HERE / 'protocol.json')
    digest = hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()
    trials = []
    for trial in protocol['episodes']:
        run = ROOT / 'runs' / trial['episode_id']
        result = dict(trial, status='missing', success=None, initial_prompt_verified=None)
        if not (run / 'outcome.json').exists():
            result['status'] = 'in_progress' if run.exists() else 'missing'
            trials.append(result)
            continue
        config = read(run / 'config.json')
        assert config['frozen_study']['protocol_sha256'] == digest
        assert config['source_hashes'] == protocol['source_hashes']
        assert config['frozen_study']['material_hashes'] == protocol['material_hashes']
        assert config['model'] == protocol['model']
        assert config['reasoning_effort'] == protocol['reasoning_effort']
        for key in ['seed', 'state_index', 'condition']:
            assert config[key] == trial[key]
        for key, value in protocol['shared'].items():
            assert config[key] == value
        outcome = read(run / 'outcome.json')
        dispatch = read(run / 'dispatch_audit.json') if (run / 'dispatch_audit.json').exists() else {}
        result['initial_prompt_verified'] = dispatch.get('initial_plaintext_verified', False)
        commands = rows(run / 'commands.jsonl')
        feedback = rows(run / 'sensor_feedback.jsonl')
        waypoints = [w for command in commands for w in
                     command['result'].get('execution_report', {}).get('waypoints', [])]
        interruptions = [c for c in commands if c['result'].get('execution_report', {}).get(
            'stop_reason') == 'armed_empty_sized_closure']
        usage = read(run / 'policy_usage.json') if (run / 'policy_usage.json').exists() else None
        replay = read(run / 'replay_verification.json') if (run / 'replay_verification.json').exists() else None
        turns = [read(f) for f in sorted(run.glob('policy_turn_*.json'))]
        assert len(turns) == len(commands) == outcome['model_calls'], 'Incomplete decision logs'
        assert sum(w['executed_steps'] for w in waypoints) == len(feedback), 'Incomplete motion feedback'
        delivery_intervals = [t['policy'].get('policy_wall_seconds') for t in turns]
        missing_delivery_intervals = sum(value is None for value in delivery_intervals)
        observed_delivery_seconds = sum(value for value in delivery_intervals if value is not None)
        delivered_policy_seconds = None if missing_delivery_intervals else observed_delivery_seconds
        command_seconds = sum(c['execution_wall_seconds'] for c in commands)
        cancelled_steps = sum(sum(w['steps'] for w in c['command']['waypoints']) -
                              sum(w['executed_steps'] for w in
                                  c['result']['execution_report']['waypoints'])
                              for c in interruptions)
        result.update(status='recorded', success=outcome['success'],
                      native_terminal_checks=outcome['diagnostic_goal_predicates'],
                      stop_reason=outcome['stop_reason'], decisions=outcome['model_calls'],
                      simulated_seconds=outcome['simulated_seconds'],
                      total_host_wall_seconds=outcome['wall_seconds'],
                      source_revision=config['code_revision'], code_dirty=config['code_dirty'],
                      waypoints=len(waypoints), armed_waypoints=sum(w['armed'] for w in waypoints),
                      empty_flagged_waypoints=sum(w['first_flags']['empty_sized_closure'] is not None
                                                  for w in waypoints),
                      interrupted_commands=len(interruptions),
                      cancelled_requested_steps=cancelled_steps,
                      cancelled_following_waypoints=sum(c['result']['execution_report'][
                          'remaining_waypoints_cancelled'] for c in interruptions),
                      flagged_empty_motion_samples=sum(bool(r['flags']['empty_sized_closure'])
                                                       for r in feedback),
                      simulator_command_seconds=command_seconds,
                      setup_wall_seconds=config['setup_wall_seconds'],
                      dispatch_to_delivered_policy_seconds=delivered_policy_seconds,
                      observed_dispatch_to_delivered_policy_seconds=observed_delivery_seconds,
                      missing_delivery_intervals=missing_delivery_intervals,
                      orchestration_residual_seconds=None if missing_delivery_intervals else
                      outcome['wall_seconds'] - config['setup_wall_seconds'] - command_seconds -
                      delivered_policy_seconds,
                      orchestration_residual_note='Includes pre-dispatch idle, root analysis, tool/orchestration '
                      'and operator pauses. Delivery and native inference clocks differ; not robot completion time.',
                      feedback_publication_seconds=sum(r['seconds'] for r in rows(
                          run / 'feedback_publication.jsonl')), usage=usage, replay=replay)
        result['infrastructure_interruptions'] = [read(f) for f in sorted(
            run.glob('infrastructure_interruption_*.json'))]
        if usage:
            result.update(inference_requests=usage['model_inference_requests'],
                          native_policy_seconds=usage['policy_wall_seconds'],
                          api_equivalent_cost_usd=usage['api_equivalent_standard_cost_usd'])
        result['boundary_audit'] = read(run / 'policy_tool_audit.json') if (
            run / 'policy_tool_audit.json').exists() else None
        trials.append(result)
    pairs = []
    for state in [1, 2]:
        group = [t for t in trials if t['paired_state'] == state and t['status'] == 'recorded']
        if len(group) != 2:
            continue
        baseline = next(t for t in group if t['condition'] == 'direct_waypoints_feedback')
        guard = next(t for t in group if t['condition'] == 'empty_closure_guard')
        initial = [np.load(ROOT / 'runs' / t['episode_id'] / 'initial_state.npy') for t in group]
        assert np.array_equal(*initial)
        initial_audit = verify_initial(state)
        matched_prompt = initial_audit['initial_prompt_matched']
        pair = dict(paired_state=state, matched_physics=True, matched_prompt=matched_prompt,
                    initial_public_inputs_verified=True,
                    interpretation='Matched mechanism comparison' if matched_prompt else
                    'Exploratory: unverified/mismatched initial prompt; no isolated mechanism attribution',
                    success_difference=int(guard['success']) - int(baseline['success']),
                    both_succeeded=guard['success'] and baseline['success'])
        for key in ['decisions', 'inference_requests', 'simulated_seconds',
                    'native_policy_seconds', 'api_equivalent_cost_usd']:
            if key in baseline and key in guard:
                pair[key + '_difference_guard_minus_timed'] = guard[key] - baseline[key]
                if pair['both_succeeded'] and pair['matched_prompt']:
                    pair[key + '_completion_ratio'] = guard[key] / baseline[key] if baseline[key] else None
        pairs.append(pair)
    summaries = {}
    for condition in protocol['conditions']:
        completed = [t for t in trials if t['condition'] == condition and t['status'] == 'recorded']
        wins = sum(t['success'] for t in completed)
        summaries[condition] = dict(scheduled=2, completed=len(completed), successes=wins,
                                   descriptive_wilson_95=interval(wins, len(completed)))
    return dict(study_id=protocol['study_id'], protocol_sha256=digest, trials=trials,
                paired_results=pairs, condition_summaries=summaries,
                statistical_scope='Retain all four scheduled outcomes. First pair is exploratory due to '
                'prompt logging/matching failure; only second pair can isolate declared interruption '
                'semantics. One clean pair cannot establish reliability or generalization. '
                'Wilson intervals are descriptive, not equivalence tests.',
                time_scope='Failed-episode resource reductions are not faster completion. Simulator '
                'physics pauses during policy inference. Native policy, execution, publication and '
                'operator/total clocks are distinct; publication is included in command elapsed time.')


if __name__ == '__main__':
    result = analyze()
    (HERE / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['condition_summaries'], indent=2))
