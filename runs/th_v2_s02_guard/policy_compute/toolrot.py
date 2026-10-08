import numpy as np
from scipy.spatial.transform import Rotation as R
h=np.array([.04376,-.04875,0]);h=h/np.linalg.norm(h);x=np.array([0,0,1]);z=-h;y=np.cross(z,x);print(R.from_matrix(np.column_stack([x,y,z])).as_quat())
