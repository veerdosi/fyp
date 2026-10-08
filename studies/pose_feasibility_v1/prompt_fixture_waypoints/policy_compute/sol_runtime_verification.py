import json, os, sys
from pathlib import Path
folder=Path(os.environ['POLICY_PUBLIC_FOLDER'])
obs=json.loads((Path(os.environ['POLICY_OBSERVATION_FOLDER'])/'observation.json').read_text())
sys.path.insert(0,str(folder/'robot_kinematics'))
from kinematic_preview import Preview
solver=Preview((folder/'robot_kinematics/robot.xml').read_text(),json.loads((folder/'robot_kinematics/parameters.json').read_text()))
p=obs['proprioception']
print(json.dumps(solver.solve(p['robot0_joint_pos'],p['robot0_eef_pos'],p['robot0_eef_quat']),sort_keys=True))
