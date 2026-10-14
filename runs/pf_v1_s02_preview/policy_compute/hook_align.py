import numpy as np
from scipy.spatial.transform import Rotation as R
q=[.828959,.559304,-.001028,-.002053]
n=np.array([.085609-.081115,.029710-.032846,1.086697-1.077298]);n/=np.linalg.norm(n)
z=np.array([0.,0.,1.]);a=np.cross(z,n);ang=np.arccos(n[2]);rot=R.from_rotvec(a/np.linalg.norm(a)*ang)
off=np.array([.0668-.040028,-.1332+.199956,1.15915-1.159238])
print('normal',n,'quat',(rot*R.from_quat(q)).as_quat(),'offset',rot.apply(off))
for d in [.035,.008,-.008]:
 hole=np.array([.085609,.029710,1.086697])+n*d
 print(d,'eef',hole-rot.apply(off))
