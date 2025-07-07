# 최근접 이웃 알고리즘 

import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier

a_x = [3,4,5,6,7]
a_y = [10,14,12,13,18]

b_x = [20,21,22,23,24]
b_y = [21,22,32,21,23]

c_x = [4,3,1,5,3]
c_y = [1,2,3,1,5]

d_x = [21,22,32,21,23]
d_y = [3,4,5,6,7]

xx = a_x + b_x + c_x + d_x
yy = a_y + b_y + c_y + d_y
# 데이터 준비

data = [[x,y] for x,y in zip(xx, yy)]
target = [0]*5 + [1]*5 + [2]*5 + [3]*5

print(data)
print(target)

kn = KNeighborsClassifier() # 객체생성 : 최근접이웃 모델 가져와
kn.fit(data,target) # 학습해라 

# # 예측하기
# result = kn.predict([[3,5], [20,22]]) 





# plt.scatter(a_x, a_y)
# plt.scatter(b_x, b_y)
# plt.scatter(c_x, c_y)
# plt.scatter(d_x, d_y)
# plt.scatter([3,2],[5,7] marker='x', color='red')
# plt.show()