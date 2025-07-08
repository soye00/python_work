from flask import Flask, render_template, request
import base64
import io
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')
from myclassfi import kn
 
app = Flask(__name__)   

@app.route("/")
def home():
    return 'Hello, I am Home!'

@app.route("/aa", methods=['GET', 'POST'])    
def aa():
    img_data = None
    result = None
    label_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}


    if request.method == 'POST':
        print(request.form['name'])
        x = int(request.form['x'])
        y = int(request.form['y'])
        result = kn.predict([[x, y]])[0]
         # 그래프 그리기
        fig, ax = plt.subplots()
        ax.scatter([3,4,5,6,7], [12,14,11,13,10], label='A')
        ax.scatter([20,21,22,23,24], [21,22,32,21,23], label='B')
        ax.scatter([4,3,1,5,3], [1,2,3,1,5], label='C')
        ax.scatter([14,13,21,15,43], [1,2,3,1,5], label='D')
        ax.scatter(x, y, color='red', s=100, label='Input', marker='x') 
        ax.legend()

        # 이미지를 메모리 버퍼에 저장
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()


    else:
        result = '없음'   
    return render_template('aa.html', result=result, img_data=img_data,label_map=label_map)

if __name__ == '__main__':
    app.run(debug=True) 