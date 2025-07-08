from flask import Flask,render_template,request

import base64
import io
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')

from ex02 import perch_length, perch_weight,kr


app = Flask(__name__)

@app.route('/',methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        print(request.form['length'])
        x = int(request.form['length'])
        y = kr.predict([[x]])

        # 그래프 그리기
        plt.scatter(perch_length, perch_weight, label='perch')
        plt.scatter(x,y)
        plt.legend()

        # 이미지를 메모리 버퍼에 저장
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
    else:
        img_data = None
    return render_template('aa.html',img_data=img_data)

if __name__ == '__main__':
    app.run(debug=True)
