import numpy as np
from scipy.spatial.transform import Rotation as R
base=np.array([-.085035,-.287636,1.170434]); tip=np.array([-.058636,-.311608,1.105577]); eef=np.array([-.093280,-.269006,1.209850])
d=(tip-base)/np.linalg.norm(tip-base); z=np.array([0,0,-1.]); axis=np.cross(d,z); ang=np.arccos(d@z); corr=R.from_rotvec(axis/np.linalg.norm(axis)*ang)
q=corr*R.from_quat([.7058297,.0003174,-.5922826,.3885944]); print('q',q.as_quat()); print('rotated tip offset',corr.apply(np.array([-.053831,-.317496,1.091878])-eef))
