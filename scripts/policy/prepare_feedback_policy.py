"""Add matched public sensor semantics to the existing fresh policy handoff."""
import json,runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
run=Path(sys.argv[1]).resolve()
sys.argv=[str(root/'scripts/policy/prepare_policy.py'),str(run)]
runpy.run_path(str(root/'scripts/policy/prepare_policy.py'),run_name='__main__')
config=json.loads((run/'config.json').read_text());obs=json.loads((run/'public/latest.json').read_text())
path=run/'policy_initial.txt';message=path.read_text()
common=(
 '\nShared processed robot feedback: every public observation folder also contains sensor_feedback.json, '
 'with current finger opening, empty-gripper-reference compensated wrench, and a compact last-motion summary. The complete 20Hz sensor rows are in sensor_feedback_samples.jsonl for optional calculations. '
 f'The shared coefficients and thresholds are in {run}/public/feedback_calibration.json. '
 'You may read those files and use them in permitted temporary calculations. Changed load, stagnant motion and empty-sized closure '
 'are observations, not object identity, acquisition, seating or task-success certificates. Wrist load does not cover every arm collision. '
 'Empty-sized closure means finger opening at or below the calibrated empty maximum plus 2mm and finger-speed norm at most 0.001m/s '
 'for three consecutive samples after at least ten steps in a waypoint. A thicker opening does not prove the intended object is secured. '
 '\nEach waypoint may include optional "abort_if_empty_close":true or false (default false). You choose whether an occupied grasp is expected '
 'and whether to arm this field on a closing/carrying waypoint. Arming requires gripper +1 and at least ten steps. '
 'Intentional empty closure remains possible with this field false. You may also use separate close/observe/move decisions instead of batching; '
 'one to four ordinary waypoints and all original budgets remain available. You choose every grasp, target, phase and recovery. '
)
if config['condition']=='empty_closure_guard':
 message=message.replace('execution does not stop adaptively or decide a new target.',
 'execution never decides a new target. On an explicitly armed stable empty-sized closure, it cancels the current and remaining waypoints '
 'and returns a fresh observation for your recovery decision; otherwise each waypoint runs its full duration.')
 common+='\nThis condition interrupts on an armed empty-sized closure. Force and stall flags are advisory; they do not stop execution. '
else:
 common+='\nThis condition reports all sensor flags at normal handoff and runs the full requested waypoint durations, including when the optional field is armed. '
message=message.replace('Interpret these images and return the next command.',common+'\nInterpret these images and return the next command.')
path.write_text(message)
