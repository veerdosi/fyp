"""Reproduce retrospective counts from original records; no policy calls."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    sources = {}
    def read(path):
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())
    coding = read(HERE / 'coding.json')
    sources[str(Path(__file__).resolve().relative_to(ROOT))] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    expected = ['pilot_tool_hang_001', 'pilot_tool_hang_002']
    for study in ['tool_hang_v1', 'tool_hang_v2', 'pose_feasibility_v1']:
        data = read(ROOT / 'studies' / study / 'results.json')
        assert data.get('complete', study == 'tool_hang_v2')
        expected.extend(row['episode_id'] for row in data['trials'])
    labels = coding['episodes']
    assert set(expected) == {row['episode'] for row in labels}
    assert len(expected) == len(labels) == 16
    episodes, reasons = [], 0
    for label in labels:
        folder = ROOT / 'runs' / label['episode']
        command_path = folder / 'commands.jsonl'
        sources[str(command_path.relative_to(ROOT))] = hashlib.sha256(command_path.read_bytes()).hexdigest()
        rows = [json.loads(line) for line in command_path.read_text().splitlines()]
        outcome = read(folder / 'outcome.json')
        assert outcome['success'] == label['success']
        assert [row['call'] for row in rows] == list(range(1, len(rows) + 1))
        assert all(row['command'].get('reason') for row in rows)
        for key in ['first_incident_decisions', 'evidence_decisions']:
            assert set(label[key]) <= {row['call'] for row in rows}
        assert (rows[-1]['command']['type'] != 'finish') == (label['completion'] == 'no_finish_budget')
        path = folder / 'steps.jsonl'
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        terminal = json.loads(path.read_text().splitlines()[-1])
        assert bool(terminal['scoring_success']) == label['success']
        reasons += len(rows)
        episodes.append(dict(episode=label['episode'], decisions=len(rows),
                             commands_path=str(command_path.relative_to(ROOT)),
                             command_type_counts=dict(Counter(r['command']['type'] for r in rows)),
                             native_terminal_checks=terminal['diagnostic_goal_predicates']))
    failed = [row for row in labels if not row['success']]
    aggregate = dict(episodes=len(labels), returned_reasons=reasons,
                     successes=sum(row['success'] for row in labels), failed_episodes=len(failed),
                     first_incident_counts=dict(Counter(row['first_incident'] for row in labels)),
                     failed_terminal_stage_counts=dict(Counter(row['terminal_stage'] for row in failed)),
                     failed_completion_counts=dict(Counter(row['completion'] for row in failed)))
    result = dict(scope=coding['scope'], aggregate=aggregate, episodes=episodes,
                  classification_source='coding.json', source_hashes=sources,
                  classification_method='Manual retrospective coding of every returned reason against execution reports and prior causal diagnoses; not keyword counting or hidden reasoning.',
                  limitations=coding['limitations'])
    (HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(aggregate, indent=2))


if __name__ == '__main__':
    main()
