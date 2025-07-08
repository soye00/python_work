a = [1,2,3,4,5]
b = [6,7,8,9,10]

import numpy as np

na = np.array([1, 2, 3, 4, 5])
nb = np.array([6, 7, 8, 9, 10])



#슬라이싱
print(a[:3])  # 리스트 슬라이싱
print(na[:3])  # NumPy 배열 슬라이싱


print(a+b)  # 리스트 덧셈
print(na+nb)  # NumPy 배열 덧셈

# print(a * b)  # 리스트 곱셈 => 요소별 곱셈이 아니라 리스트의 반복
print(na * nb)  # NumPy 배열 곱셈