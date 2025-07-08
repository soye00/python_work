aa = [1,2,3,4,5,6]

print(aa)

# aa.reshape(2,3)  # 2행 3열로 변환
# TypeError: 'list' object has no attribute 'reshape'

import numpy as np

aa = np.array(aa)  # 리스트를 NumPy 배열로 변환
aa = aa.reshape(3,2)  # 2행 3열로 변환 , (3,-1) -1로 하면 자동으로 계산됨 
print(aa)
