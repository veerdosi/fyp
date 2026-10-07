import numpy as np,json
from scipy.spatial.transform import Rotation as R
p='/Users/veerdosi/Documents/code/github/fyp/runs/th_v1_s02_phase_guard/public/obs_0004/'
s=json.load(open(p+'sense_007.json'))['points']; o=json.load(open(p+'observation.json'))['proprioception']
a,b,t=[np.array(s[i]['world_xyz']) for i in range(3)]
v=(b-a)/np.linalg.norm(b-a); axis=np.cross(v,[0,0,1]); angle=np.arctan2(np.linalg.norm(axis),v[2]); rot=R.from_rotvec(axis/np.linalg.norm(axis)*angle)
e=np.array(o['robot0_eef_pos']); delta=rot.apply(a-e)
new=np.array([t[0],t[1],0.985])-delta
print('quat', (rot*R.from_quat(o['robot0_eef_quat'])).as_quat().tolist());print('eef target',new.tolist())
