import numpy as np
from scipy.spatial.transform import Rotation as R
d=np.array([-.055703,-.002368,1.05235])-np.array([-.075833,.033351,1.137473]);d=d/np.linalg.norm(d)
a=np.cross(d,[0,0,-1]);ang=np.arccos(-d[2]);rot=R.from_rotvec(a/np.linalg.norm(a)*ang)
q=R.from_quat([.7065846,.0000758,-.6217543,.3378753]);print('q', (rot*q).as_quat())
p=np.array([-.080893,.042999,1.159963]);tip=np.array([-.050987,-.013053,1.030491]);newrel=rot.apply(tip-p);print('tip relative',newrel);print('eef for tip .99',np.array([-.079,.044,.99])-newrel)
