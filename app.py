from flask import Flask, render_template, request, jsonify ,redirect
app = Flask(__name__)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient('mongodb+srv://sparta:test@cluster0.clljnvr.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

import hashlib
import datetime
import jwt

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/call_login')
def call_login():  
    return render_template('login.html')

@app.route('/call_register')
def call_register():  
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash})

    return jsonify({'msg': '가입에 성공했습니다.'})

SECRET_KEY = "mingyu"

# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
       
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=5)    #언제까지 유효한지
        }
        #jwt를 암호화
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # print(token)

        # token을 줍니다.
        return jsonify({'msg': '로그인에 성공했습니다.','result': 'success' ,'token': token})
    # 찾지 못하면
    else:
        return jsonify({'msg': '아이디/비밀번호가 일치하지 않습니다.', 'result': 'fail'})
    
@app.route('/call_index')
def after_login():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        return render_template('index.html')
    
    except jwt.ExpiredSignatureError:
        return redirect("login.html")
    except jwt.exceptions.DecodeError:
        return redirect("login.html")

     

@app.route("/movie", methods=["POST"])
def movie_post():
    url_receive = request.form['url_give']
    comment_receive = request.form['comment_give']
    star_receive = request.form['star_give']

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive,headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    ogtitle= soup.select_one('meta[property="og:title"]')['content']
    ogiamge= soup.select_one('meta[property="og:image"]')['content']
    ogdesc= soup.select_one('meta[property="og:description"]')['content']

    
    doc = {
        'title': ogtitle,
        'desc':ogdesc,
        'image':ogiamge,
        'comment' : comment_receive,
        'star' : star_receive
    }
    
    db.movies.insert_one(doc)

    return jsonify({'result':'저장완료'})

@app.route("/movie", methods=["GET"])
def movie_get():
    all_movies = list(db.movies.find({},{'_id':False}))

    return jsonify({'result':all_movies})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)