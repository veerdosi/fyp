import numpy as np
from scipy.spatial.transform import Rotation as R
p=np.array([-.092723,.076826,1.004417]); top=np.array([-.094534,.092035,1.096005]); d=p-top; d/=np.linalg.norm(d)
t=np.array([0,0,-1]); ax=np.cross(d,t); rot=R.from_rotvec(ax/np.linalg.norm(ax)*np.arccos(d@t))
e=np.array([-.116809,.102119,1.189768]); q=np.array([.641840,.114829,-.715421,.251055]); p2=e+rot.apply(p-e)
print('q', (rot*R.from_quat(q)).as_quat());print('eef',e+np.array([-.080-p2[0],.046-p2[1],-.020]));print('p2',p2)
