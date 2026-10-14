"""Correct derived delivery aggregates when a recovered interval is unavailable."""
import argparse
import json
from pathlib import Path


def finalize(run):
    path = run / 'diagnostic_summary.json'
    summary = json.loads(path.read_text())
    policies = [json.loads(p.read_text()).get('policy', {})
                for p in sorted(run.glob('policy_turn_*.json'))]
    missing = [index + 1 for index, policy in enumerate(policies)
               if policy.get('policy_wall_seconds') is None]
    clocks = summary['wall_time_components']
    clocks['missing_delivery_interval_decisions'] = missing
    recovery = run / 'recovery_note.json'
    if recovery.exists():
        clocks['host_clock_approximate_and_interrupted'] = bool(
            json.loads(recovery.read_text()).get('host_clock_approximate_and_interrupted'))
        if clocks['host_clock_approximate_and_interrupted']:
            clocks['note'] += (' Host origin was reconstructed approximately after '
                               'process loss; elapsed and residual clocks cannot '
                               'establish completion speed.')
    if missing:
        clocks['recorded_delivery_interval_subtotal_seconds'] = sum(
            p['policy_wall_seconds'] for p in policies
            if p.get('policy_wall_seconds') is not None)
        for key in ['policy_dispatch_to_delivered_response_seconds',
                    'residual_operator_and_orchestration_seconds',
                    'delivered_response_minus_native_turn_seconds']:
            clocks[key] = None
        clocks['note'] = ('At least one dispatch/delivery interval is unavailable; '
                          'its duration is not zero. Complete delivery aggregates '
                          'and residuals are unknown. Native completed-turn time '
                          'is separately measured. Interrupted host elapsed '
                          'cannot establish completion speed.')
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps(clocks, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    finalize(parser.parse_args().run)
