"""Verify saved initial public inputs; preserve the first dispatch erratum."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GUARD_EXECUTION = ('execution never decides a new target. On an explicitly armed stable empty-sized '
                   'closure, it cancels the current and remaining waypoints and returns a fresh '
                   'observation for your recovery decision; otherwise each waypoint runs its full duration.')
TIMED_EXECUTION = 'execution does not stop adaptively or decide a new target.'
GUARD_CONDITION = ('This condition interrupts on an armed empty-sized closure. Force and stall '
                   'flags are advisory; they do not stop execution.')
TIMED_CONDITION = ('This condition reports all sensor flags at normal handoff and runs the full '
                   'requested waypoint durations, including when the optional field is armed.')


def read(path):
    return json.loads(path.read_text())


def normalized_prompt(run):
    text = (run / 'policy_initial.txt').read_text()
    config = read(run / 'config.json')
    expected = GUARD_EXECUTION if config['condition'] == 'empty_closure_guard' else TIMED_EXECUTION
    condition = GUARD_CONDITION if config['condition'] == 'empty_closure_guard' else TIMED_CONDITION
    assert text.count(expected) == text.count(condition) == 1
    return text.replace(str(run), 'EPISODE_PATH').replace(run.name, 'EPISODE_ID').replace(
        expected, 'DECLARED_EXECUTION_SEMANTICS').replace(condition, 'DECLARED_CONDITION_SEMANTICS')


def verify(state):
    runs = [ROOT / 'runs' / f'th_v2_s{state:02d}_{condition}' for condition in ['timed', 'guard']]
    if not all((run / 'policy_initial.txt').exists() for run in runs):
        return None
    initial_exact = np.array_equal(*[np.load(run / 'initial_state.npy') for run in runs])
    files = ['agentview.png', 'robot0_eye_in_hand.png', 'agentview_depth_m.npy',
             'robot0_eye_in_hand_depth_m.npy', 'calibration.json', 'sensor_feedback_samples.jsonl']
    checks = {name: (runs[0] / 'public/obs_0000' / name).read_bytes() == (
        runs[1] / 'public/obs_0000' / name).read_bytes() for name in files}
    observations = [read(run / 'public/obs_0000/observation.json')['proprioception'] for run in runs]
    feedback = []
    for run in runs:
        f = read(run / 'public/obs_0000/sensor_feedback.json')
        f.pop('calibration_file')
        f.pop('samples_file')
        feedback.append(f)
    calibration_exact = (runs[0] / 'public/feedback_calibration.json').read_bytes() == (
        runs[1] / 'public/feedback_calibration.json').read_bytes()
    prompt_verified = []
    for run in runs:
        audit = read(run / 'dispatch_audit.json') if (run / 'dispatch_audit.json').exists() else {}
        verified = audit.get('initial_plaintext_verified', False)
        if verified:
            assert audit['initial_plaintext_sha256'] == hashlib.sha256((run / 'policy_initial.txt').read_bytes()).hexdigest()
        prompt_verified.append(verified)
    prompt_match = state == 2 and all(prompt_verified) and normalized_prompt(runs[0]) == normalized_prompt(runs[1])
    result = dict(paired_state=state, initial_physics_exact=initial_exact, public_file_checks=checks,
                  initial_proprioception_exact=observations[0] == observations[1],
                  processed_feedback_exact=feedback[0] == feedback[1], calibration_exact=calibration_exact,
                  saved_dispatch_plaintext_verified=prompt_verified, initial_prompt_matched=prompt_match,
                  prompt_scope='Manual saved-before-dispatch verification; native task archives are encrypted.',
                  prompt_erratum='amendment_002_encrypted_input_erratum.json' if state == 1 else None)
    assert initial_exact and all(checks.values()) and result['initial_proprioception_exact']
    assert result['processed_feedback_exact'] and calibration_exact
    if state == 2:
        assert prompt_match, 'Second pair common instructions or dispatch accounting differ'
    (HERE / f'paired_initial_{state:02d}.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps([result for state in [1, 2] if (result := verify(state))], indent=2))
