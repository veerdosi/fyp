import json,os,sys
from pathlib import Path
p=Path(os.environ['POLICY_PUBLIC_FOLDER']); o=json.loads((Path(os.environ['POLICY_OBSERVATION_FOLDER'])/'observation.json').read_text())
sys.path.insert(0,str(p/'robot_kinematics'))
from kinematic_preview import Preview
v=Preview((p/'robot_kinematics/robot.xml').read_text(),json.loads((p/'robot_kinematics/parameters.json').read_text()))
for pos,q in [([.075,.03,.985],[0,-.707107,0,.707107]),([.03,.03,.985],[.707107,0,.707107,0]),([-.02,.03,.965],[.707107,0,.707107,0]),([.04,-.12,1.1],[.707107,0,.707107,0])]:
 print(pos,q,v.solve(o['proprioception']['robot0_joint_pos'],pos,q)['best'])
