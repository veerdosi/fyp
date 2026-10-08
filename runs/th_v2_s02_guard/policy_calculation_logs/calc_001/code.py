import numpy as np
from scipy.spatial.transform import Rotation as R
a=np.array([-.05495707937,.01247932531,1.06939970476]); b=np.array([-.05914841946,.02485316012,1.10718589479]);d=(a-b)/np.linalg.norm(a-b);z=np.array([0,0,-1]);v=np.cross(d,z);r=R.from_rotvec(v/np.linalg.norm(v)*np.arccos(d@z));q=R.from_quat([.7069481,.00026323,-.6326652,.316163]);p=np.array([-.07392073,.04492006,1.18001648]);tip=np.array([-.05269605,.0035849,1.04642449]);print('q', (r*q).as_quat());print('tip_rotated',p+r.apply(tip-p))
