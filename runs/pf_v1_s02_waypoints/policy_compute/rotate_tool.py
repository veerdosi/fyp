import numpy as np
from scipy.spatial.transform import Rotation as R
p=np.array([.033260961,-.217224325,1.008189089]); c=np.array([(.0602009764+.0816553164)/2,(-.1302046231-.1402173812)/2,1.00338]);v=c-p
a=v/np.linalg.norm(v);b=np.array([0,0,1]);axis=np.cross(a,b);r=R.from_rotvec(axis/np.linalg.norm(axis)*np.arccos(a@b));q=(r*R.from_quat([.843590849,.536986246,-.000153951,.000475832])).as_quat()
print('q',q,'offset',r.apply(v))
