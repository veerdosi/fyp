import numpy as np
from scipy.spatial.transform import Rotation as R
p=np.array([-.053669,.019931,1.030156]); top=np.array([-.065530,.029289,1.070371]); d=p-top; d/=np.linalg.norm(d)
t=np.array([0,0,-1]); ax=np.cross(d,t); angle=np.arccos(d@t); rot=R.from_rotvec(ax/np.linalg.norm(ax)*angle)
e=np.array([-.078867,.046014,1.139941]); q=np.array([.706759,.000065,-.622521,.336094])
p2=e+rot.apply(p-e); target=e+np.array([-.0796-p2[0],.045-p2[1],0])
print('orientation', (rot*R.from_quat(q)).as_quat());print('eef target', target);print('transformed shaft point',p2)
