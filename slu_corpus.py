from flask import Flask, request, session, render_template, redirect, url_for, flash, g, make_response
from flask_bootstrap import Bootstrap
import flask_login
import hashlib
import pymysql
import os
from db_helper import DB_Helper
from flask_paginate import Pagination
from datetime import timedelta, datetime
import json
import time


app = Flask(__name__)
Bootstrap(app)
app.secret_key = os.urandom(24)
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=2)




# 사용자 클래스
class user_class:
    def __init__(self, user_id, pw_hash=None, authenticated=False):
        self.user_id = user_id
        self.pw_hash = pw_hash
        self.authenticated = authenticated

    def can_login(self, pw_hash):
        return self.pw_hash == pw_hash

    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    @classmethod
    def get(cls, user_id):
        pw_hash = users[user_id].pw_hash
        return cls(user_id, pw_hash)



login_manager = flask_login.LoginManager()
login_manager.init_app(app)



def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = pymysql.connect(host='163.239.169.54',
                             port=3306,
                             user='s20131533',
                             passwd='s20131533',
                             db='slu_corpus',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)
        g._database = db
    else:
        db.ping()

    return db



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()




@login_manager.user_loader
def user_loader(user_id):
     return user_class.get(user_id)


@app.route('/logout')
@flask_login.login_required
def logout():
    # session['logged_in'] = False
    # session.pop('username', None)
    # session.pop('password', None)

    user = flask_login.current_user
    user.authenticated = False
    flask_login.logout_user()

    flash('로그아웃 되었습니다.', 'alert-success')
    return render_template('login_form.html', is_exist_id=1)


@app.route('/login', methods=['GET'])
def login():
    return render_template('login_form.html', is_exist_id=1)


@app.route('/login_check', methods=['POST', 'GET'])
def login_check():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    if request.method == 'POST':

        global users
        users = {}

        # DB에 저장된 user 정보 받아와서 users 딕셔너리에 저장
        rows = db_helper.select_every_rows_from_table('users')
        for row in rows:
            users[row['user_id']] = user_class(row['user_id'], pw_hash=row['user_pw'])


        user_id = request.form['id']
        user_pw = request.form['pw']

        # 비밀번호 인코딩
        user_pw = user_pw.encode('utf-8')

        # 비밀번호에 해시함수 적용
        user_pw_hash = hashlib.sha512(user_pw).hexdigest()


        if user_id not in users:
            return render_template('login_form.html', is_exist_id=0)

        # 유저이름과 그에 해당하는 패스워드가 일치하는지 확인
        if users[user_id].can_login(user_pw_hash):

            # session['logged_in'] = True
            # session['username'] = request.form['username']
            # session['password'] = request.form['password']

            users[user_id].authenticated = True
            flask_login.login_user(users[user_id])
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=6)

            return redirect(url_for('text_board', page=1, col_name='article_id', asc1_desc0='1'))

        else:
            error_msg = '로그인 정보가 맞지 않습니다.'
            flash(error_msg, 'alert-danger')
            return render_template('login_form.html', is_exist_id=1)


    elif request.method == 'GET':
        return render_template('login_form.html')



@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)


    if request.method == 'GET':
        return render_template('sign_up.html')

    elif request.method == 'POST':

        user_id = request.form['id']
        user_pw = request.form['pw']

        # 비밀번호 인코딩
        user_pw = user_pw.encode('utf-8')

        # 비밀번호에 해시함수 적용
        user_pw_hash = hashlib.sha512(user_pw).hexdigest()


        user_name = request.form['username']
        user_birth = request.form['birth']
        user_gender = request.form['gender']
        user_email = request.form['email']

        user_info_dict = {}
        user_info_dict['user_id'] = user_id
        user_info_dict['user_pw'] = user_pw_hash
        user_info_dict['user_name'] = user_name
        user_info_dict['user_birth'] = user_birth
        user_info_dict['user_gender'] = user_gender
        user_info_dict['user_email'] = user_email

        db_helper.insert_user_info(user_info_dict)

        flash('회원가입 되었습니다.', 'alert-success')
        return render_template('login_form.html')


@app.route('/overlap_check', methods=['POST'])
def overlap_check():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    user_id = request.form['id']

    if user_id.strip() == '':
        return 'empty'

    user_list = db_helper.select_one_column('user_id', 'users')
    for i in user_list:
        if i['user_id'] == user_id:
            return 'fail'

    return 'success'



@login_manager.unauthorized_handler
def unauthorized():
    flash('자동 로그아웃 되었습니다. 다시 로그인 해주세요.', 'alert-danger')
    return render_template('login_form.html')


# ===================================================================================================================
# ===================================================================================================================
# ===================================================================================================================


def reload_text_board():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    #user_id = flask_login.current_user.user_id
    user_id = 'chris'

    '''
    if search_msg == 'None' or search_msg == '':
        search_msg = None
    '''

    #article_id = request.args.get('article_id')
    #article_id = None


    rows_category = db_helper.select_table('category')
    rows_topic = db_helper.select_table('topic')
    rows_act = db_helper.select_table('act')

    #if article_id == 'None' or article_id == '':
    #    article_id = None



    # 1 이면 숫자 포함한 문장만 보여주고 0이면 숫자 없는 문장만 보여준다
    #inc_num = request.args.get('inc_num')



    # 공통 코드 ==========================================
    #page = request.args.get('page', type=int, default=1)
    #per_page = 10

    asc1_desc0 = request.args.get('asc1_desc0')
    print('asc1_desc0 : ' + str(asc1_desc0))
    if asc1_desc0 == None:
        asc1_desc0 = '0'
    col_name = request.args.get('col_name')
    print('col_name : ' + str(col_name))
    if col_name == None:
        col_name = 'id'
    # ===================================================




    board_total = []
    rows_speech = db_helper.select_table('speech')
    for row_speech in rows_speech:
        temp = {}
        speech_id = row_speech['id']
        temp['id'] = speech_id
        temp['speech'] = row_speech['speech']

        act_id = row_speech['act_id']
        row_act = db_helper.select_row_by_id('act', act_id)
        temp['act'] = row_act['act']

        topic_id = row_act['topic_id']
        category_id = row_act['category_id']
        domain_id = row_act['domain_id']

        row_topic = db_helper.select_row_by_id('topic', topic_id)
        temp['topic'] = row_topic['topic']

        row_category = db_helper.select_row_by_id('category', category_id)
        temp['category'] = row_category['category']

        rows_slot_value = db_helper.select_rows_by_condition('speech_id', 'slot_value', speech_id)
        slot_value = []
        for row_slot_value in rows_slot_value:
            each_slot_value = {}
            value_id = row_slot_value['value_id']
            slot_id = row_slot_value['slot_id']

            row_slot = db_helper.select_row_by_id('slot', slot_id)
            slot = row_slot['slot']
            row_value = db_helper.select_row_by_id('value', value_id)
            value = row_value['value']

            each_slot_value[slot] = value
            slot_value.append(each_slot_value)

        temp['slot_value'] = slot_value

        # 각 row의 정보 삽입
        board_total.append(temp)


    if asc1_desc0 == '0':
        print('내림차순 정렬, 기준 칼럼 : id')
        board_total = sorted(board_total, key=lambda x:x['id'], reverse=True)
    elif asc1_desc0 == '1':
        print('오름차순 정렬, 기준 칼럼 : id')
        board_total = sorted(board_total, key=lambda x:x['id'])
    else:
        print("SOMETHING IS WRONG CHECK HERE !!!!!!!!!!")


    print((board_total))


    rows_slot = db_helper.select_table('slot')
    rows_slot_jsonstr = json.dumps(rows_slot)

    return render_template('text_board.html',
                           board_total=board_total,
                           user_id=user_id,
                           asc1_desc0=asc1_desc0,
                           col_name=col_name,
                           #inc_num=inc_num,
                           rows_category=rows_category,
                           rows_topic=rows_topic,
                           rows_act=rows_act,
                           rows_slot=rows_slot,
                           rows_slot_jsonstr=rows_slot_jsonstr)






@app.route('/text_board', methods = ['GET'])
#@flask_login.login_required
def text_board():
    print(request.method + '\t' + request.url)

    #user_id = flask_login.current_user.user_id

    return reload_text_board()







'''
@app.route('/text_board/edit', methods=['GET'])
@flask_login.login_required
def text_edit():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    user_id = flask_login.current_user.user_id
    #user_id = ''

    page = request.args.get('page')
    sent_id = request.args.get('sent_id')
    article_id = request.args.get('article_id')
    search_msg = request.args.get('search_msg')
    session['sent_id'] = sent_id
    where_to = request.args.get('where_to')
    is_all_sents = request.args.get('is_all_sents')
    ############################################################################### 여기부터

    if article_id == '' or article_id == 'None':
        article_id = None

    print(request.url)
    print('edit page' + str(request.args.get('page')))
    print('article id: ' + str(article_id))
    print('sent id : ' + str(sent_id))

    sent_modified_date = db_helper.select_data_from_table_by_id('sent_modified_date', 'SentenceTable', sent_id)
    sent_converted_count = db_helper.select_data_from_table_by_id('sent_converted_count', 'SentenceTable', sent_id)

    original_text = db_helper.select_data_from_table_by_id('sent_original', 'SentenceTable', sent_id)


    # 문장에 포함된 숫자를 한글로 변환
    #converted_list = NumberToWord(original_text)
    #converted_text = "\n".join(converted_list)

    is_bef_exist = 0
    is_aft_exist = 0

    if article_id is not None:
        # (만약 기사를 클릭했다면) 클릭한 문장의 전 문장 정보
        bef_clicked_row = db_helper.select_before_row_from_sentence(sent_id, article_id)
    elif article_id is None:
        # (기사를 클릭하지 않은 경우) 클릭한 문장의 전 문장 정보
        bef_clicked_row = db_helper.select_before_row_from_sentence(sent_id, None)


    if bef_clicked_row != None:
        is_bef_exist = 1

        # 왼쪽 화살표 버튼 클릭시
        if where_to == 'bef':
            sent_id = bef_clicked_row['sent_id']
            return redirect(url_for('text_edit',
                                    article_id=article_id,
                                    sent_id=sent_id,
                                    search_msg=search_msg,
                                    where_to=None))



    if article_id is not None:
        # (만약 기사를 클릭했다면) 클릭한 문장의 다음 문장 정보
        aft_clicked_row = db_helper.select_after_row_from_sentence(sent_id, article_id)
    elif article_id is None:
        # (기사를 클릭하지 않은 경우) 클릭한 문장의 다음 문장 정보
        aft_clicked_row = db_helper.select_after_row_from_sentence(sent_id, None)

    if aft_clicked_row != None:
        is_aft_exist = 1

        if where_to == 'aft':
            sent_id = aft_clicked_row['sent_id']
            return redirect(url_for('text_edit',
                                    article_id=article_id,
                                    sent_id=sent_id,
                                    search_msg=search_msg,
                                    where_to=None))




    if search_msg is not None:
        return render_template('text_edit.html',
                               original_text=original_text,
                               #converted_text=converted_text,
                               page=page,
                               search_msg=search_msg,
                               article_id=article_id,
                               sent_id=sent_id,
                               user_id=user_id,
                               sent_modified_date=sent_modified_date,
                               sent_converted_count=sent_converted_count,
                               is_bef_exist=is_bef_exist,
                               is_aft_exist=is_aft_exist)
    else:
        return render_template('text_edit.html',
                               original_text = original_text,
                               #converted_text = converted_text,
                               page = page,
                               article_id=article_id,
                               sent_id=sent_id,
                               user_id=user_id,
                               sent_modified_date=sent_modified_date,
                               sent_converted_count=sent_converted_count,
                               is_bef_exist=is_bef_exist,
                               is_aft_exist=is_aft_exist)
'''






@app.route('/<board_type>/delete/<id>', methods=['POST'])
#@flask_login.login_required
def delete(board_type, id):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    print(request.url)
    print(request.method)


    #id = request.form['id']
    table_name = request.form['table_name']


    if table_name == 'act':
        # act 테이블의 해당 id 삭제
        try:
            #id = request.form['act_id']
            db_helper.delete_row_by_id('act', id)
            return redirect(url_for('act_manage_board'))
        # 자식을 먼저 삭제하라는 pymysql 에러가 발생하면
        except:
            return redirect(url_for('act_manage_board', delete_error=1))

    elif table_name == 'speech':
        try:
            #id = request.form['speech_id']
            row_speech = db_helper.select_row_by_id('speech', id)
            # 삭제할 speech의 act_id
            act_id = row_speech['act_id']
            # act_count 1 감소
            db_helper.update_act_count(act_id, 0)
            # speech 테이블의 해당 id 삭제 (speech를 삭제하면 slot_value 테이블의 해당 speech_id인 row들도 같이 삭제되도록 on delete cascade 설정해 놓았다.)
            db_helper.delete_row_by_id('speech', id)
            return redirect(url_for('text_board'))
        except:
            return redirect(url_for('text_board'))




'''
@app.route('/<board_type>/search', methods=['GET'])
@flask_login.login_required
def search(board_type):

    #article_id = request.args.get('article_id')
    search_msg = request.args.get('search_msg')


    #print("article id: " + str(article_id))
    print("search msg: " + search_msg)


    if board_type == 'article_board':
        return redirect(url_for('article_board', search_msg=search_msg))
    elif board_type == 'text_board':
        #return redirect(url_for('text_board', search_msg=search_msg, article_id=article_id))
        return redirect(url_for('text_board', search_msg=search_msg))
'''


'''
@app.route('/<board_type>/order', methods=['GET'])
@flask_login.login_required
def order(board_type):

    page = request.args.get('page')
    col_name = request.args.get('col_name')
    asc1_desc0 = request.args.get('asc1_desc0')
    search_msg = request.args.get('search_msg')
    article_id = request.args.get('article_id')
    inc_num = request.args.get('inc_num')
    sid1 = request.args.get('sid1')
    sid2 = request.args.get('sid2')


    if board_type == 'article_board':
        if sid1 != 'undefined':
            return redirect(url_for('article_board', col_name=col_name, asc1_desc0=asc1_desc0, page=page, search_msg=search_msg, sid1=sid1, sid2=sid2))
        else:
            return redirect(url_for('article_board', col_name=col_name, asc1_desc0=asc1_desc0, page=page, search_msg=search_msg))


    elif board_type == 'text_board':
        if article_id != 'undefined':
            return redirect(url_for('text_board', col_name = col_name, asc1_desc0 = asc1_desc0, page = page, search_msg=search_msg, article_id=article_id, inc_num=inc_num))
        else:
            return redirect(url_for('text_board', col_name=col_name, asc1_desc0=asc1_desc0, page=page, search_msg=search_msg, inc_num=inc_num))
'''


@app.route('/export', defaults={'button_type':''})
@app.route('/export/<button_type>', methods=['GET', 'POST'])
#@flask_login.login_required
def export(button_type):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)
    #user_id = flask_login.current_user.user_id
    user_id = 'chris'

    if request.method == 'GET':
        return render_template('export.html', user_id=user_id)

    elif request.method == 'POST':
        fromdate = request.form['fromdate_hid']
        todate = request.form['todate_hid']
        sid1 = request.form['sid1']

        try:
            sid2 = request.form['sid2']
        # sid2를 선택하지 않은 경우, 즉 sid1이 '전체' 인 경우
        except:
            sid2 = None


        original_json_list = []
        converted_json_list = []


        # Only 카테고리 조건
        if fromdate == '' and todate == '':
            if sid2 is not None:
                if sid2 == '전체':
                    article_rows = db_helper.select_article_with_sid1(sid1)
                else:
                    article_rows = db_helper.select_article_with_sid1_sid2(sid1, sid2)
            elif sid2 is None:
                article_rows = db_helper.select_article_with_no_cond()

        # 날짜 조건 + 카테고리 조건
        else:
            if sid2 is not None:
                if sid2 == '전체':
                    article_rows = db_helper.select_article_with_date_sid1(sid1, fromdate, todate)
                else:
                    article_rows = db_helper.select_article_with_date_sid1_sid2(sid1, sid2, fromdate, todate)
            elif sid2 is None:
                article_rows = db_helper.select_article_with_date(fromdate, todate)



        # '원본 저장' 버튼 클릭시 수행
        if button_type == 'original':
            for article_row in article_rows:
                temp_dict = {}
                temp_list = []

                temp_dict['article_aid'] = article_row['article_aid']
                temp_dict['article_url'] = article_row['article_url']
                temp_dict['article_title'] = article_row['article_title']
                temp_dict['article_uploaded_date'] = str(article_row['article_uploaded_date'])
                temp_dict['article_collected_date'] = str(article_row['article_collected_date'])
                temp_dict['article_sid1'] = article_row['article_sid1']
                temp_dict['article_sid2'] = article_row['article_sid2']

                sentence_rows = db_helper.select_every_rows_from_sentence_by_id(article_row['article_id'])
                for sentence_row in sentence_rows:
                    temp_list.append(sentence_row['sent_original'])

                temp_dict['sentences'] = temp_list

                original_json_list.append(temp_dict)


            # 조건에 의해 검색된 결과가 없다면
            if not original_json_list:
                return render_template('export.html', nothing_searched=1, user_id=user_id)

            original_json = json.dumps(original_json_list, indent=4, ensure_ascii=False, sort_keys=True)

            response = make_response(original_json)
            response.headers['Content-Disposition'] = "attachment; filename=original.json"

            return response


        # '변환 저장' 버튼 클릭시 수행
        elif button_type == 'converted':
            for article_row in article_rows:

                sentence_rows = db_helper.select_every_rows_from_sentence_by_id(article_row['article_id'])
                for sentence_row in sentence_rows:
                    temp_dict = {}
                    temp_dict['input'] = sentence_row['sent_original']
                    temp_dict['output'] = sentence_row['sent_converted']
                    converted_json_list.append(temp_dict)


            if not converted_json_list:
                return render_template('export.html', nothing_searched=1, user_id=user_id)


            # ensure_ascii 옵션을 False로 설정해주니 다운로드한 json파일에서 한글이 제대로 보인다.
            converted_json = json.dumps(converted_json_list, indent=4, ensure_ascii=False, sort_keys=True)


            response = make_response(converted_json)
            # 헤더를 이런식으로 설정하면 다운로드 창이 뜬다
            response.headers['Content-Disposition'] = "attachment; filename=converted.json"
            return response




@app.route('/act_manage_board', methods=['GET'])
def act_manage_board():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    is_delete_error = request.args.get('delete_error')
    asc1_desc0 = request.args.get('asc1_desc0')
    if asc1_desc0 == None:
        asc1_desc0 = '0'
    col_name = request.args.get('col_name')
    if col_name == None:
        col_name = 'id'

    rows_category = db_helper.select_table('category')

    board_total = []
    rows_act = db_helper.select_table('act')
    for row_act in rows_act:
        temp = {}
        temp['id'] = row_act['id']
        temp['act'] = row_act['act']
        temp['act_count'] = row_act['act_count']
        category_id = row_act['category_id']
        row_category = db_helper.select_row_by_id('category', category_id)
        temp['category'] = row_category['category']

        topic_id = row_act['topic_id']
        row_topic = db_helper.select_row_by_id('topic', topic_id)
        temp['topic'] = row_topic['topic']

        board_total.append(temp)


    if asc1_desc0 == '0':
        print('내림차순 정렬, 기준 칼럼 : ' + col_name)
        board_total = sorted(board_total, key=lambda x:x[col_name], reverse=True)
    elif asc1_desc0 == '1':
        print('오름차순 정렬, 기준 칼럼 : ' + col_name)
        board_total = sorted(board_total, key=lambda x:x[col_name])
    else:
        print("SOMETHING IS WRONG CHECK HERE !!!!!!!!")




    return render_template('act_manage_board.html',
                           board_total=board_total,
                           col_name=col_name,
                           asc1_desc0=asc1_desc0,
                           rows_act=rows_act,
                           rows_category=rows_category,
                           is_delete_error=is_delete_error)




@app.route('/ajax_find_topic', methods=['POST'])
def ajax_find_topic():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    res = {}
    res['success'] = True

    # act_manage_board 에서 ajax로 보낸 cat값
    category = request.form['category']
    category_id = 0

    rows_category = db_helper.select_table('category')
    for row_category in rows_category:
        # 선택한 category에 해당하는 category id 찾기
        if row_category['category'] == category:
            category_id = row_category['id']
            break

    temp = []
    rows_topic = db_helper.select_table('topic')
    for row_topic in rows_topic:
        # 선택한 category에 해당하는 topic들 선택
        if row_topic['category_id'] == category_id:
            temp.append(row_topic['topic'])


    res['topic'] = temp
    print(temp)

    return json.dumps(res)



@app.route('/ajax_add_act', methods=['POST'])
def ajax_add_act():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    res = {}
    res['success'] = True
    res['act_overlap'] = False

    category = request.form['category']
    rows_category = db_helper.select_rows_by_condition('category', 'category', category)
    # 새로운 category가 입력되면 새로 추가
    if len(rows_category) == 0:
        db_helper.insert_new_category(category)
        rows_category = db_helper.select_rows_by_condition('category', 'category', category)
        # 새로 등록된 category의 id
        category_id = rows_category[0]['id']
    else:
        # 기존 category의 id
        category_id = rows_category[0]['id']

    topic = request.form['topic']
    topic_id = 0

    # 선택한 category에 해당하는 topic들
    rows_topic = db_helper.select_rows_by_condition('category_id', 'topic', category_id)
    is_exist_topic = 0
    for row_topic in rows_topic:
        # 이미 topic이 존재한다면
        if row_topic['topic'] == topic:
            is_exist_topic = 1
            topic_id = row_topic['id']
            break

    # 새로운 topic이 입력되면 새로 추가
    if is_exist_topic == 0:
        db_helper.insert_new_topic(topic, category_id)
        rows_topic = db_helper.select_rows_by_condition('category_id', 'topic', category_id)
        for row_topic in rows_topic:
            if row_topic['topic'] == topic:
                topic_id = row_topic['id']
                break


    act = request.form['act']

    # act 중복 검사
    rows_act = db_helper.select_rows_by_condition('act', 'act', act)
    # 중복이라면 중복 알림
    if len(rows_act) > 0:
        res['is_act_overlapped'] = True
        return json.dumps(res)


    db_helper.insert_new_act(act, topic_id, category_id)

    rows_act = db_helper.select_rows_by_condition('act', 'act', act)
    act_id = rows_act[0]['id']
    res['id'] = act_id
    res['act'] = act
    res['category'] = category
    res['topic'] = topic


    return json.dumps(res)


@app.route('/ajax_find_by_act', methods=['POST'])
def ajax_find_by_act():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    res = {}
    res['success'] = True

    act = request.form['act']
    rows_act = db_helper.select_rows_by_condition('act', 'act', act)

    topic_id = rows_act[0]['topic_id']
    row_topic = db_helper.select_row_by_id('topic', topic_id)
    topic = row_topic['topic']

    category_id = rows_act[0]['category_id']
    row_category = db_helper.select_row_by_id('category', category_id)
    category = row_category['category']

    res['act'] = act
    res['category'] = category
    res['topic'] = topic

    return json.dumps(res)


@app.route('/ajax_add_speech', methods=['POST'])
def ajax_add_speech():

    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    res = {}
    res['success'] = True

    print(request.form)

    act = request.form['act']
    rows_act = db_helper.select_rows_by_condition('act', 'act', act)
    act_id = rows_act[0]['id']


    category = request.form['category']
    topic = request.form['topic']
    user_speech = request.form['user_speech']

    # speech 추가
    db_helper.insert_new_speech(user_speech, act_id)
    row_speech = db_helper.select_latest_row('speech')
    inserted_speech_id = row_speech['id']
    res['id'] = inserted_speech_id

    # 추가한 speech에 해당하는 act의 act_count 1 증가
    db_helper.update_act_count(act_id, 1)
    row_act = db_helper.select_row_by_id('act', act_id)
    res['act_count'] = row_act['act_count']

    rows_slot = db_helper.select_table('slot')
    res['rows_slot'] = rows_slot

    # slot_value 는 JSON 문자열
    slot_value = request.form['slot_value']

    # 원래 형식인 리스트로 변환
    slot_value = json.loads(slot_value)
    for each in slot_value:
        slot = list(each.items())[0][0]
        value = list(each.items())[0][1]

        # 초기화
        value_id = 0

        # ================ 우선 slot 과 value 존재 여부에 따른 처리 ================ #
        # slot이 존재하면
        try:
            rows_slot = db_helper.select_rows_by_condition('slot', 'slot', slot)
            slot_id = rows_slot[0]['id']

            # slot에 해당하는 후보 value들
            rows_value = db_helper.select_rows_by_condition('slot_id', 'value', slot_id)
            is_new_value = 1
            for row_value in rows_value:
                # 이미 등록된 value
                if row_value['value'] == value:
                    is_new_value = 0
                    value_id = row_value['id']
                    break

            # 기존에 없는 새로운 value 라면 추가
            if is_new_value == 1:
                db_helper.insert_new_value(value, slot_id)
                rows_value = db_helper.select_rows_by_condition('slot_id', 'value', slot_id)
                for row_value in rows_value:
                    if row_value['value'] == value:
                        value_id = row_value['id']


        # 존재하지 않는 slot이면 slot과 value 각각 새로 추가
        except:
            # 새로운 slot 추가
            db_helper.insert_new_slot(slot)
            rows_slot = db_helper.select_rows_by_condition('slot','slot',slot)
            # 새로 추가한 slot의 id
            slot_id = rows_slot[0]['id']
            # 새로 추가한 slot 에 해당하는 새로운 value 추가
            db_helper.insert_new_value(value, slot_id)
            rows_value = db_helper.select_rows_by_condition('slot_id', 'value', slot_id)
            value_id = rows_value[0]['id']
        # ================ 우선 slot 과 value 존재 여부에 따른 처리 ================ #





        # ================ 그 다음 slot-value 테이블에 slot-value 쌍 삽입 ================ #

        db_helper.insert_new_slot_value(inserted_speech_id, slot_id, value_id)

        # ================ 그 다음 slot-value 테이블에 slot-value 쌍 삽입 ================ #



    return json.dumps(res)



@app.route('/export_all', methods=['POST'])
def export_all():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    all_corpus_data = []

    rows_speech = db_helper.select_table('speech')
    for row_speech in rows_speech:

        each_utterance = {}
        each_utterance['session_id'] = None

        utters = []
        each_utters = {}

        speech_id = row_speech['id']
        speech = row_speech['speech']
        act_id = row_speech['act_id']
        row_act = db_helper.select_row_by_id('act', act_id)

        act = row_act['act']

        topic_id = row_act['topic_id']
        row_topic = db_helper.select_row_by_id('topic', topic_id)
        topic = row_topic['topic']

        category_id = row_act['category_id']
        row_category = db_helper.select_row_by_id('category', category_id)
        category = row_category['category']


        dialog_acts = []
        each_dialog_acts = {}
        rows_slot_value = db_helper.select_rows_by_condition('speech_id', 'slot_value', speech_id)
        # slot_value 쌍이 없는 경우
        if len(rows_slot_value) == 0:
            each_dialog_acts['act'] = act
            each_dialog_acts['slot'] = None
            each_dialog_acts['value'] = None
            dialog_acts.append(each_dialog_acts)
        # slot_value 쌍이 존재하는 경우
        else:
            for row_slot_value in rows_slot_value:
                each_dialog_acts = {}

                slot_id = row_slot_value['slot_id']
                row_slot = db_helper.select_row_by_id('slot', slot_id)
                slot = row_slot['slot']

                value_id = row_slot_value['value_id']
                row_value = db_helper.select_row_by_id('value', value_id)
                value = row_value['value']

                each_dialog_acts['act'] = act
                each_dialog_acts['slot'] = slot
                each_dialog_acts['value'] = value

                dialog_acts.append(each_dialog_acts)


        each_utters['dialog_acts'] = dialog_acts
        each_utters['semantic_tagged'] = None
        each_utters['speaker'] = "User"
        each_utters['text'] = speech
        each_utters['text_spaced'] = None
        each_utters['category'] = category
        each_utters['topic'] = topic
        each_utters['turn_index'] = '1'

        utters.append(each_utters)

        each_utterance['utters'] = utters

        all_corpus_data.append(each_utterance)


    all_corpus_json = json.dumps(all_corpus_data, indent=4, ensure_ascii=False, sort_keys=True)
    print(all_corpus_json)

    current_date = datetime.today().strftime('%Y-%m-%d__%H-%M-%S')
    corpus_data_cnt = len(all_corpus_data)

    filename = 'slu_corpus_data__cnt' + str(corpus_data_cnt) + '__' + current_date + '.json'

    res = make_response(all_corpus_json)
    res.headers['Content-Disposition'] = "attachment; filename=" + filename

    return res


# ==================================================================================================================================





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)