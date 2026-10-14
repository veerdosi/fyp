import numpy as np
from scipy.spatial.transform import Rotation as R
v=np.array([-.0213373748,-.1144901716,1.0777971862])-np.array([-.0899058434,-.2547655788,1.0800008864])
a=v/np.linalg.norm(v); b=np.array([0.,0.,-1.]); cross=np.cross(a,b)
r=R.from_rotvec(cross/np.linalg.norm(cross)*np.arccos(a@b))
q=(r*R.from_quat([.8435607644,.5370336880,-.0001991457,.0001225436])).as_quat()
print('q',q,'length',np.linalg.norm(v),'rotated_tip',r.apply(v))
