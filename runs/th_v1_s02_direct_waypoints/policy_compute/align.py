import numpy as np
from scipy.spatial.transform import Rotation as R
p=np.array([-.0309888776,-.0335203481,1.2005503895]); tip=np.array([-.0641921626,.0066018198,1.056427292]); top=np.array([-.0418406234,-.0167640555,1.1440819667])
d=(tip-top)/np.linalg.norm(tip-top); target=np.array([0,0,-1]); axis=np.cross(d,target); angle=np.arctan2(np.linalg.norm(axis),np.dot(d,target)); rot=R.from_rotvec(axis/np.linalg.norm(axis)*angle)
q=rot*R.from_quat([.6470030934,-.2899900955,-.6441685288,-.2869488596]); off=rot.apply(tip-p)
print('q',q.as_quat(),'offset',off,'pose for tip at opening plus 25mm',np.array([-.080,.044,.985])-off)
