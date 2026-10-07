import os,json,numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation as R
p=os.environ['POLICY_OBSERVATION_FOLDER']; c=json.load(open(p+'/calibration.json'))['agentview']; a=np.array(Image.open(p+'/agentview.png')); d=np.load(p+'/agentview_depth_m.npy'); v,u=np.indices(d.shape); T=np.array(c['camera_to_world']); f=c['intrinsic'][0][0]; xyz=np.stack([(u-128)*d/f,(v-128)*d/f,d],-1)@T[:3,:3].T+T[:3,3]
m=(u>82)&(u<110)&(v>92)&(v<108)&(a[:,:,0]>a[:,:,2]*1.5)&(a[:,:,0]>60)&(xyz[:,:,2]>1.05)
x=xyz[m]; center=x.mean(0); _,_,vh=np.linalg.svd(x-center); axis=vh[0]; axis*=np.sign(axis[1]); print('rod center',center,'axis',axis,'n',len(x))
q=np.array(json.load(open(p+'/observation.json'))['proprioception']['robot0_eef_quat']); goal=np.array([0,0,-1.]); rot=R.from_rotvec(np.cross(axis,goal)/np.linalg.norm(np.cross(axis,goal))*np.arccos(axis@goal)); print('upright quat',(rot*R.from_quat(q)).as_quat()); print('transformed rodcenter offset',rot.apply(center-np.array([-.09191,-.25776,1.07999])))
