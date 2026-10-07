import numpy as np,json
from scipy.spatial.transform import Rotation as R
p='/Users/veerdosi/Documents/code/github/fyp/runs/th_v1_s02_phase_guard/public/obs_0012/'
o=json.load(open(p+'observation.json'))['proprioception'];s=json.load(open(p+'sense_018.json'))['points']
h=np.mean([s[i]['world_xyz'] for i in range(2,6)],axis=0);e=np.array(o['robot0_eef_pos']);n=np.array([.357,-.934,0]);n=n/np.linalg.norm(n)
r=R.from_matrix(np.column_stack([np.cross([0,0,1],n),[0,0,1],n]))
print('quat',(r*R.from_quat(o['robot0_eef_quat'])).as_quat().tolist());print('offset',r.apply(h-e).tolist());print('target eef',(np.array([-.065,-.045,1.046])-r.apply(h-e)).tolist())
