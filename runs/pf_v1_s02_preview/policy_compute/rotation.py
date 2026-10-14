from scipy.spatial.transform import Rotation as R
q=[.585866627,.395148325,-.587065538,.394933096]
print((R.from_rotvec([.15,-.04,0])*R.from_quat(q)).as_quat())
