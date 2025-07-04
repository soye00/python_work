import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

#도미 데이터
bream_length = [25.4, 26.3, 26.5, 29.0, 29.0, 29.7, 29.7, 30.0, 30.0, 30.7, 31.0, 31.0, 31.5, 32.0, 32.0, 32.0, 33.0, 33.0, 33.5, 33.5, 34.0, 34.0, 34.5, 35.0, 35.0, 35.0, 35.0, 36.0, 36.0, 37.0, 38.5, 38.5, 39.5, 41.0, 41.0]
bream_weight = [242.0, 290.0, 340.0, 363.0, 430.0, 450.0, 500.0, 390.0, 450.0, 500.0, 475.0, 500.0, 500.0, 340.0, 600.0, 600.0, 700.0, 700.0, 610.0, 650.0, 575.0, 685.0, 620.0, 680.0, 700.0, 725.0, 720.0, 714.0, 850.0, 1000.0, 920.0, 955.0, 925.0, 975.0, 950.0]

#빙어 데이터
smelt_length = [9.8, 10.5, 10.6, 11.0, 11.2, 11.3, 11.8, 11.8, 12.0, 12.2, 12.4, 13.0, 14.3, 15.0]
smelt_weight = [6.7, 7.5, 7.0, 9.7, 9.8, 8.7, 10.0, 9.9, 9.8, 12.2, 13.4, 12.2, 19.7, 19.9]

# plt.scatter([1,2,3,10,20],[200,300,300,200,400])
# plt.plot([1,2,3,10,20],[200,300,300,200,400], color='red', linestyle='--', linewidth=2)
# plt.title('Scatter Plot with Line') 
# plt.bar([1,2,3,10,20],[200,300,300,200,400], color='green', alpha=0.5)
# plt.xlabel('X')
# plt.ylabel('Y')    
# plt.grid(True)
# plt.legend(['Data Points', 'Line', 'Bar'])  

length = bream_length + smelt_length
weight = bream_weight + smelt_weight    

# 리스트 컴프리헨션  [표현식 for 변수 in 반복가능한_객체]
# for l,w in zip(length, weight):
#     print('l',l)
#     print('w', w)

# 데이터 전처리 
fish_data = [(l, w) for l, w in zip(length, weight)]
fish_taget = [1]*35 + [0]*14  # 도미는 1, 빙어는 0

kn = KNeighborsClassifier()
kn.fit(fish_data, fish_taget)
# 예측.. 학습해라 
new_fish = [[30, 600], [10, 12]]  # 새로운 물고기 데이터
predicted = kn.predict(new_fish)  

print(predicted)  # 예측 결과 출력
# 예측 결과를 시각화
print("Predicted classes for new fish:", predicted)
# 시각화
plt.scatter(bream_length, bream_weight, color='blue', label='Bream')    
plt.scatter(smelt_length, smelt_weight, color='orange', label='Smelt')
plt.scatter([30, 10], [600, 12], color='red', label='New Fish', marker='x', s=100)  # 새로운 물고기 데이터
plt.title('도미데이터 빙어데이터')
plt.xlabel('Length (cm)')
plt.ylabel('Weight (g)')
plt.grid(True)
plt.legend()


print(fish_data)
print(fish_taget)   

# print([1]*10)
# print([1]*5 + [2]*3)

# print(len(bream_length), len(smelt_length))
# print(len(length))
# print('length', length)
# print("weight", weight)


# plt.scatter(bream_length, bream_weight, color='blue', label='Bream')
# plt.scatter(smelt_length, smelt_weight, color='orange', label='Smelt')
# plt.title('Bream Length vs Weight')
# plt.xlabel('Length (cm)')   
# plt.ylabel('Weight (g)')
# plt.grid(True)

plt.show()