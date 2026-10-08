import numpy as np
from scipy.spatial.transform import Rotation as R
a=np.array([-.0682627154,.0348911631,1.0017381613]);b=np.array([-.0694724496,.0380474092,1.0313449434]);d=(a-b)/np.linalg.norm(a-b);z=np.array([0,0,-1]);v=np.cross(d,z);r=R.from_rotvec(v/np.linalg.norm(v)*np.arccos(d@z));q=R.from_quat([.71279785,.11598575,-.66180887,.20118535]);p=np.array([-.08025558,.04354247,1.11987756]);print((r*q).as_quat());print('axis point after correction',p+r.apply(a-p))
