import sqlite3
from flask import Flask,redirect, url_for, render_template,request,session


app = Flask(__name__)
app.secret_key = '1234'

@app.route('/')
def loginpage():
    return render_template('login_page.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup_page.html')

#회원가입
@app.route('/signup',methods = ['POST','GET'])
def create_user():
    if request.method=='POST':
        try:
            nickname= request.form['nickname']
            email = request.form['email']
            password=request.form['password']

            with sqlite3.connect('photo_album.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO user_table(user_nickname,user_ID,user_PW) VALUES (?,?,?)" ,(nickname,email,password))
                con.commit()
        except:
            con.rollback()
        finally:
            if con:
                con.close()
            return render_template("login_page.html")

#로그인 구현
@app.route('/login',methods=['POST','GET'])
def check_user():
    if request.method=='POST':
            email=request.form['email']
            password= request.form['password']

            with sqlite3.connect('photo_album.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM user_table WHERE user_ID = ? AND user_PW = ?", (email, password))
                user = cur.fetchone()

                if user:
                    session['user_id'] =user[0]
                    session['user_nickname'] = user[1]
                    return redirect(url_for('mainpage'))
                else:
                    return render_template("loginpage.html")

#사진 디테일 페이지로 리다이렉트
@app.route('/photo_detail/<int:item_id>')
def photo_detail(item_id):
    with sqlite3.connect('photo_album.db') as con:
        cur = con.cursor()
        cur.execute('''
            SELECT DM_table.DM_ID, DM_table.DM_msg, user_table.user_nickname
            FROM DM_table
            JOIN user_table ON DM_table.user_ID = user_table.ID
            WHERE DM_table.photo_ID = ?
        ''', (item_id,))
        dms = cur.fetchall()
    cur.execute('''
            SELECT photo_img, user_table.user_nickname, photo_describ
            FROM photo_table
            JOIN user_table ON photo_table.user_ID = user_table.ID
            WHERE photo_ID = ?
        ''', (item_id,))
    photo = cur.fetchone()

    item = {
        'id': item_id,
        'author': photo[1],
        'keywords': '#키워드',
        'description': photo[2],
        'img_src': 'photo[0]'
    }
    return render_template('photo_detail.html', item=item, dms=dms)

#DM 메시지 저장
@app.route('/msg_send', methods=['POST'])
def msg_send():
    
    user_id = session['user_id']
    dm_msg = request.form['msg']
    photo_id=request.form['photo_id']

    with sqlite3.connect('photo_album.db') as con:
        cur = con.cursor()
        cur.execute('''
            INSERT INTO DM_table (user_ID, photo_ID, DM_msg) VALUES (?, ?, ?)
                    ''', (user_id, 1,dm_msg))
        con.commit()
    
    return redirect(url_for('photo_detail',item_id=1))

#DM 삭제
@app.route('/delete_dm/<int:dm_id>', methods=['POST'])
def delete_dm(dm_id):
    if 'user_id' not in session:
        return redirect(url_for('check_user'))

    user_id = session['user_id']

    with sqlite3.connect('photo_album.db') as con:
        cur = con.cursor()
        cur.execute('DELETE FROM DM_table WHERE DM_ID = ? AND user_ID = ?', (dm_id, user_id))
        con.commit()

    photo_id = request.form['photo_id']
    return redirect(url_for('photo_detail', item_id=photo_id))

#업로드 페이지로 렌더링
@app.route('/upload_page')
def upload_page():
    user_nickname = session['user_nickname']
    return render_template('photo_upload.html', user_nickname=user_nickname)

@app.route('/mainpage')
def mainpage():
    with sqlite3.connect('photo_album.db') as con:
        cur = con.cursor()
        cur.execute('''
            SELECT photo_table.photo_ID, photo_table.photo_img, user_table.user_nickname, 
                GROUP_CONCAT(photo_keyword_table.keyword), photo_table.photo_describ
            FROM photo_table
            JOIN user_table ON photo_table.user_ID = user_table.ID
            LEFT JOIN photo_keyword_table ON photo_table.photo_ID = photo_keyword_table.photo_ID
            GROUP BY photo_table.photo_ID
        ''')
        photos = cur.fetchall()

    return render_template('mainpage.html', photos=photos)


@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('loginpage'))

    user_id = session['user_id']
    photo = request.files['photo']
    keyword = request.form['key']
    description = request.form['des']

    # 사진을 저장할 경로 설정
    photo_path = f'static/uploads/{photo.filename}'
    photo.save(photo_path)
    photo_path= f'uploads/{photo.filename}'
    with sqlite3.connect('photo_album.db') as con:
        cur = con.cursor()

        # photo_table에 데이터 삽입
        cur.execute('''
            INSERT INTO photo_table (user_ID, photo_img, photo_describ)
            VALUES (?, ?, ?)
        ''', (user_id, photo_path, description))

        # 삽입된 photo ID 가져오기
        photo_id = cur.lastrowid

        # photo_keyword_table에 데이터 삽입
        cur.execute('''
            INSERT INTO photo_keyword_table (photo_ID, keyword)
            VALUES (?, ?)
        ''', (photo_id, keyword))

        con.commit()

    return redirect(url_for('loginpage'))

@app.route('/dm_list')
def dm_list():
    return render_template('dm_list.html')

if __name__ == '__main__':
    app.run(debug=True)


