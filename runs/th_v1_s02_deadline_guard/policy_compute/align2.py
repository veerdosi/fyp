import numpy as np
from scipy.spatial.transform import Rotation as R
p=np.array([-.063616,.040900,1.029143]); b=np.array([-.068967,.044392,1.088494]); e=np.array([-.065534,.051058,1.139707]);d=(p-b)/np.linalg.norm(p-b); axis=np.cross(d,[0,0,-1]);corr=R.from_rotvec(axis/np.linalg.norm(axis)*np.arccos(-d[2]));print((corr*R.from_quat([.638326,.170113,-.705104,.257740])).as_quat()); print(corr.apply(p-e))
