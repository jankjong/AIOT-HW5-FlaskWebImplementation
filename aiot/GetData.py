from flask import Flask,render_template

app = Flask(__name__)


@app.route('/')
def index():
    data = {
        'text1':'对数折线图',
        'data1':[1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
    }
    return render_template('logrithm_index.html',**data)

if __name__ == '__main__':
    app.run(debug=True)

