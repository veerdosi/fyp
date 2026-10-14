from scipy.spatial.transform import Rotation as R
q=[.624924,.431270,-.543590,.357752]
print(R.from_quat(q).as_matrix())
