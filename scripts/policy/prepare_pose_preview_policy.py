"""Save matched public policy materials with only the query capability differing."""
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[2]
run=Path(sys.argv[1]).resolve()
sys.argv=[str(ROOT/'scripts/policy/prepare_feedback_policy.py'),str(run)]
runpy.run_path(str(ROOT/'scripts/policy/prepare_feedback_policy.py'),run_name='__main__')
path=run/'policy_initial.txt'
s=path.read_text()
s=s.replace('execution does not stop adaptively or decide a new target.',
    'execution never decides a new target. In both conditions, explicitly armed stable empty-sized closure cancels the current and remaining waypoints and returns control to you; otherwise waypoints run their full duration.')
s=s.replace('This condition reports all sensor flags at normal handoff and runs the full requested waypoint durations, including when the optional field is armed.',
    'In both conditions an armed empty-sized closure interrupts execution. Force and stall flags remain advisory.')
s=s.replace('do not import fyp, mujoco or robosuite','do not import fyp or robosuite')
common=(f'\nKnown robot kinematics: {run}/public/robot_kinematics contains robot.xml, parameters.json and kinematic_preview.py. '
    'These are read-only public mechanical/calculation materials, available in both conditions. Fresh genuine robot0_joint_pos encoder angles are in observation.json. '
    'You may import mujoco solely to compile and calculate with this supplied robot-only model; no live simulator, scene model, task objects, scoring or private state access is permitted. '
    'You may import the provided public kinematic_preview.py helper into a logged temporary calculation and use its Preview class: '
    'Preview(robot_xml_text,parameters).solve(current_joint_angles,candidate_world_position,candidate_quaternion_xyzw). '
    'The bounded solver tries four fixed seeds with 1mm/0.01rad tolerance and a one-degree joint margin. It finds geometric pose solutions, not motion paths. '
    'No solution is only a bounded search result; a solution is not collision clearance, grasp retention, dynamic arrival or task completion. '
    'You choose every candidate pose, executed target and recovery. Every ordinary move still uses the same OSC_POSE controller. ')
enabled=json.loads((run/'config.json').read_text())['pose_preview']['enabled']
capability=('\nCondition capability: optional {"type":"preview","poses":[{"position":[x,y,z],"quaternion_xyzw":[qx,qy,qz,qw]}],"reason":"..."} queries one to four candidate poses using current robot angles. '
    'Quaternion may be omitted to use current orientation. This consumes one decision, advances no physics and returns a structured calculation file. It neither cancels execution nor chooses a replacement target.' if enabled else
    '\nCondition capability: use ordinary move, sense and finish commands. There is no structured preview command; the same public robot model/helper and logged temporary calculations remain available.')
s=s.replace('Interpret these images and return the next command.',common+capability+'\nInterpret these images and return the next command.')
path.write_text(s)
(run/'policy_condition_capability.txt').write_text(capability)
print('Saved exact policy text:',path)
