import numpy as np
from scipy.spatial.transform import Rotation as R
q=[.708814,.705384,-.002234,-.003348]; e=np.array([.065158,-.207761,1.159272]); hole=np.array([.068,-.123298,1.15064]); rot=R.from_euler('x',90,degrees=True)
off=rot.apply(hole-e); print('q',(rot*R.from_quat(q)).as_quat());print('offset',off);print('eef',np.array([-.077,-.070,1.041])-off)
