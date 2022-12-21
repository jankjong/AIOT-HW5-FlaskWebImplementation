# -*- coding: utf-8 -*-
import json
import numpy as np
import pandas as pd
from   pandas import DataFrame as df
from   six.moves import urllib
import pymysql.cursors
from   sklearn.linear_model import LogisticRegression as LR
from   flask import Flask, render_template, jsonify
import pickle
import gzip

app = Flask(__name__)

def connectDB():
    myserver   = "localhost"
    myuser     = "test123"
    mypassword = "test123"
    mydb       = "aiotdb"    
    debug      = 0
    conn = pymysql.connect(host=myserver,user=myuser, passwd=mypassword, db=mydb)
    return conn, debug

def fetchCursorFromTable(conn, tablename):
    c = conn.cursor()
    c.execute("SELECT * FROM {}".format(tablename))
    #====== 取回所有查詢結果 ======#
    results = c.fetchall()
    print(type(results))
    print(results[:10])
    data_df = df(list(results),columns=['id','time','value','temp','humi','status'])
    return c, data_df

@app.route("/data.json")
def data():
    timeInterval = 1000
    data = pd.DataFrame()
    featureList = ['market-price', 'trade-volume']
    for feature in featureList:
        url = "https://api.blockchain.info/charts/"+feature+"?timespan="+str(timeInterval)+"days&format=json"
        data['time'] = pd.DataFrame(json.loads(urllib.request.urlopen(url).read().decode('utf-8'))['values'])['x']*1000
        data[feature] = pd.DataFrame(json.loads(urllib.request.urlopen(url).read().decode('utf-8'))['values'])['y']
    result = data.to_dict(orient='records')
    seq = [[item['time'], item['market-price'], item['trade-volume']] for item in result]
    return jsonify(seq)
 
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/indexAI")
def indexAI():
    return render_template('indexAI.html')

@app.route("/indexNoAI")
def indexNoAI():
    return render_template('indexNoAI.html')

@app.route("/getData")
def getData():
    # 連線資料庫，返回連線物件。
    conn, debug = connectDB()
    c = conn.cursor()
    # Step 1. 讀取資料。
    c, test_df = fetchCursorFromTable(conn, "sensors")
    c.close()
    conn.close()

    # Step 2. 將讀取資料結果，合成 json 格式，傳回 Hightchart
    result = test_df.to_dict(orient='records')
    seq = [[item['id'], item['time'], item['value'], item['temp'], item['humi'], item['status']] for item in result]
    return jsonify(seq)

@app.route("/getRandom")
def getRandom():
    # 連線資料庫，返回連線物件。
    conn, debug = connectDB()
    c = conn.cursor()
    # if debug:
    #     input("pause.. conn.cursor() ok.......")
    # Step 1. 先將資料庫打亂。
    c.execute("update sensors set status = RAND()")
    conn.commit()
    
    # Step 2. 再讀取資料。
    c, test_df = fetchCursorFromTable(conn, "sensors")
    c.close()
    conn.close()

    # Step 3. 將讀取資料結果，合成 json 格式，傳回 Hightchart
    result = test_df.to_dict(orient='records')
    seq = [[item['id'], item['time'], item['value'], item['temp'], item['humi'], item['status']] for item in result]
    return jsonify(seq)

@app.route("/getPredict")
def getPredict():
    # 連線資料庫，返回連線物件。
    conn, debug = connectDB()

    # Step 1. 先讀取資料。
    c, test_df = fetchCursorFromTable(conn, "sensors")

    # Step 2. 讀取預訓練模型 myModel.pgz。
    with gzip.open('./model/myModel.pgz', 'r') as f:
        model = pickle.load(f)   

    # Step 3. 在 Flask console 印前 10 筆資料，確認資料讀的出來。
    print(test_df.head(10))
    if debug:
        input("pause..  show original one above (NOT correct).......")

    # Step 4. 用預訓練模型來分類。
    testX = test_df['value'].values.reshape(-1,1)
    testY = model.predict(testX)
    print(model.score(testX,testY))

    # Step 5. 在 Flask console 印前 10 筆分類結果，確認資料有被分類。
    test_df['status']=testY
    print(test_df.head(10))
    # if debug:
    #     input("pause.. now show correct one above.......")

    # Step 6. 在用分類結果，更新資料庫前，先把原本亂的值，把非 0 的重設為 0。
    c.execute('update sensors set status=0 where value > 0')

    # Step 7. 依分類結果，挑出所有值為 1 的記錄 ID 數列。
    id_list=list(test_df[test_df['status']==1].id)
    print(id_list)

    # Step 8. 將分類結果為 1 的，重新寫入資料庫。    
    for _id in id_list:
        c.execute('update sensors set status=1 where id = '+str(_id))

    # Step 9. 確認所有更新結果。
    conn.commit()
    c.close()
    conn.close()
    # if debug:
    #     input("pause ....update ok..........")
    # Step 10. 將分類結果，合成 json 格式，傳回 Hightchart
    print(test_df.head(10))
    result = test_df.to_dict(orient='records')
    seq = [[item['id'], item['time'], item['value'], item['temp'], item['humi'], item['status']] for item in result]
    return jsonify(seq)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

