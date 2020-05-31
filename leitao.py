from flask import Flask,render_template,jsonify,request
app = Flask(__name__)
import pymysql
from flask_cors import CORS
CORS(app)


# 数据库连接
db = pymysql.connect(host="10.141.209.224", user="root", password="sdzh521", db="guns", charset='utf8')
cursor = db.cursor()

@app.route('/market/', methods=['GET'])
def market():
    cursor.execute("SELECT market_code,market_name,train_id FROM `info_market`")
    res = cursor.fetchall()
    name_arr = []
    code_arr = []

    for line in res:
        code = line[0]
        name = line[1]
        train_id = line[2]
        print(train_id)
        # name = '快客便利店('+name+')'
        if train_id == 0:
            print(name)
            name_arr.append(name)
            print(code)
            code_arr.append(code)
    return jsonify({'code':code_arr,'name':name_arr})


@app.route('/site/', methods=['GET'])
def site_view():
    siteId = (int)(request.args.get('id'))
    print(siteId)
    cursor.execute("SELECT lon_lan FROM `info_market` WHERE market_id = %s", siteId)
    lon_lan = cursor.fetchone()
    return jsonify({'lat':lon_lan[0].split(',')[1],'lng':lon_lan[0].split(',')[0],"success": 0,"message": "请求成功。"})


@app.route('/lei/')
def lei_view():
    print('lei used')
    return render_template('routeOriginal.html')

@app.route('/zhuangche/')
def delivey_view_zhua():
    return render_template('load2.html')

@app.route('/pick/')
def delivey_view_pick():
    return render_template('dynamic_pick22.html')

from flask_sqlalchemy import SQLAlchemy
import traceback
import datetime
import json
DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = 'sdzh521'
HOST = '10.141.209.224'
PORT = '3306'
DATABASE = 'guns'
SQLALCHEMY_DATABASE_URI = '{}+{}://{}:{}@{}:{}/{}?charset=utf8'.format(
    DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE
)
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 5
keys = [k for k in globals() if k.isupper()]
config_dic = {k:globals()[k] for k in keys}
# app.config.from_object('settings')
app.config['JSON_AS_ASCII'] = False
app.config.update(config_dic)
CORS(app,supports_credentials=True)
db = SQLAlchemy(app)
class Traces(db.Model):
    __tablename__ = "info_vehicletrace_history"
    vehicletrace_id = db.Column(db.Integer, name='vehicletraceid', primary_key=True, autoincrement=True, nullable=False)
    train_id = db.Column(db.Integer, name='trainid', nullable=True)
    vehicle_id = db.Column(db.Integer, name='vehicleid', nullable=True)
    # longitude = db.Column(db.String(255), name='longitude', nullable=True)
    # latitude = db.Column(db.Integer, name='latitude', nullable=True)
    time = db.Column(db.DateTime, name='time', nullable=True)
    cur_load = db.Column(db.Float, name='cur_load', nullable=True)
    cur_volume = db.Column(db.Float, name='cur_volume', nullable=True)
    dispatchid = db.Column(db.Integer, name='dispatchid', nullable=True)
    lastshop = db.Column(db.Integer, name='last_shop', nullable=True)
    next_shops = db.Column(db.String, name='next_shops', nullable=True)
    next_orders = db.Column(db.String, name='next_orders', nullable=True)

@app.route('/view/trace')
def view():
    result = {}
    try:
        base_query = db.session.query(Traces)
        stops = base_query.all()
        result['msg'] = "success"
        data = [st.__dict__ for st in stops]
        for item in data:
            item.pop('_sa_instance_state')
        # Session =  db.session()

        vehicle2state = {}
        for d in data:
            v_id = d['vehicle_id']
            if v_id not in vehicle2state:
                vehicle2state[v_id] = {}
                vehicle2state[v_id]['volume'] = {}
                vehicle2state[v_id]['load'] = {}
                vehicle2state[v_id]['last_stop'] = {}
            cur_time = (d['time'] - datetime.datetime(1970, 1, 1)).seconds
            volume = d['cur_volume']
            load = d['cur_load']
            last_stop = d['lastshop']
            vehicle2state[v_id]['last_stop'][cur_time] =last_stop
            vehicle2state[v_id]['volume'][cur_time] = volume
            vehicle2state[v_id]['load'][cur_time] = load
        data_dict = {}
        for k in vehicle2state:
            data_dict[k] = {}
            volume_dic = vehicle2state[k]['volume']
            load_dic = vehicle2state[k]['load']
            lastshop_dic = vehicle2state[k]['last_stop']
            volumes = [round(volume_dic[t],1) for t in sorted(volume_dic.keys())]
            loads = [round(load_dic[t],1) for t in sorted(load_dic.keys())]
            laststops = [lastshop_dic[t] for t in sorted(lastshop_dic.keys())]
            data_dict[k]['load'] = loads
            data_dict[k]['volume'] = volumes
            data_dict[k]['last_shop'] = laststops
        result['data'] = data_dict
        result['success'] = 0
        db.session.close()
    except Exception as e:
        tb = traceback.format_exc()
        f = open("log.log", mode="a")
        f.write(str(datetime.datetime.now())+'\n')
        f.write(tb)
        f.close()
        # msg = e.args[0]
        result['msg'] = tb
        result['success'] = 1
        db.session.close()
        return json.dumps(result, ensure_ascii=False)

    return json.dumps(result, ensure_ascii=False, default=str)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5303)
