from flask import Flask, request, session, render_template, redirect, url_for, flash, g, make_response
from flask_bootstrap import Bootstrap
import flask_login
import hashlib
import pymysql
import os
from db_helper import DB_Helper
from flask_paginate import Pagination
from datetime import timedelta
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


sid1_count = {'정치' : 0, '경제' : 0, '사회' : 0, '생활/문화' : 0, '세계' : 0, 'IT/과학' : 0}

sid2_count = {'청와대' : 0, '국회/정당' : 0, '북한' : 0, '행정' : 0, '국방/외교' : 0, '정치 일반' : 0,
              '금융' : 0, '증권' : 0, '산업/재계' : 0, '중기/벤처' : 0, '부동산' : 0, '글로벌 경제' : 0, '생활경제' : 0, '경제 일반' : 0,
              '사건사고' : 0, '교육' : 0, '노동' : 0, '언론' : 0, '환경' : 0, '인권/복지' : 0, '식품/의료' : 0, '지역' : 0, '인물' : 0, '사회 일반' : 0,
              '건강정보' : 0, '자동차/시승기' : 0, '도로/교통' : 0, '여행/레저' : 0, '음식/맛집' : 0, '패션/뷰티' : 0, '공연/전시' : 0, '책' : 0, '종교' : 0, '날씨' : 0, '생활문화 일반' : 0,
              '아시아/호주' : 0, '미국/중남미' : 0, '유럽' : 0, '중동/아프리카' : 0, '세계 일반' : 0,
              '모바일' : 0, '인터넷/SNS' : 0, '통신/뉴미디어' : 0, 'IT 일반' : 0, '보안/해킹' : 0, '컴퓨터' : 0, '게임/리뷰' : 0, '과학 일반' : 0}


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


def reload_text_board(search_msg):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    #user_id = flask_login.current_user.user_id
    user_id = 'chris'

    if search_msg == 'None' or search_msg == '':
        search_msg = None

    sid1 = None
    sid2 = None
    #article_id = request.args.get('article_id')
    article_id = None


    rows_category = db_helper.select_table('category')
    rows_topic = db_helper.select_table('topic')
    rows_act = db_helper.select_table('act')

    if article_id == 'None' or article_id == '':
        article_id = None

    if article_id is not None:
        sid1 = db_helper.select_data_from_table_by_id('article_sid1', 'ArticleTable', article_id)
        sid2 = db_helper.select_data_from_table_by_id('article_sid2', 'ArticleTable', article_id)


    '''
    # 딕셔너리 초기화
    for i in sid1_count:
        sid1_count[i] = 0
    for i in sid2_count:
        sid2_count[i] = 0



    # article_sid1 각각의 개수 저장
    article_sid1_column = db_helper.select_one_column('article_sid1', 'ArticleTable')
    for row in article_sid1_column:
        key = row['article_sid1']

        if key != '':
            sid1_count[key] += 1


    # article_sid2 각각의 개수 저장
    article_sid2_column = db_helper.select_one_column('article_sid2', 'ArticleTable')
    for row in article_sid2_column:
        key = row['article_sid2']

        if key != '':
            sid2_count[key] += 1
    '''

    # 1 이면 숫자 포함한 문장만 보여주고 0이면 숫자 없는 문장만 보여준다
    inc_num = request.args.get('inc_num')



    # 공통 코드 ==========================================
    page = request.args.get('page', type=int, default=1)
    per_page = 10

    asc1_desc0 = request.args.get('asc1_desc0')
    col_name = request.args.get('col_name')
    # ===================================================



    # ===================================================
    # 문장 게시판 종류(sentence_board_type)
    # 1. 전체 문장 + 검색
    # 2. 기사 클릭
    # 3. 기사 클릭 + 검색
    # 4. 전체 문장
    # ===================================================


    # 모든 기사에서 검색한 게시글 반환
    if search_msg is not None and article_id is None:
        print('기사 전체 검색')
        sentence_board_type = 1

        search_msg_escaped = db_conn.escape_string(search_msg)
        total_count = db_helper.total_count_text_search(search_msg_escaped, inc_num)

        inc_num_0_count = db_helper.total_count_text_search(search_msg_escaped, '0')
        inc_num_1_count = db_helper.total_count_text_search(search_msg_escaped, '1')
        inc_num_none_count = db_helper.total_count_text_search(search_msg_escaped, None)


        article_title = None
        if article_id is not None:
            article_title = db_helper.select_data_from_table_by_id('article_title', 'ArticleTable', article_id)


        board_search = db_helper.call_search_sentence(page, per_page, search_msg_escaped, asc1_desc0, col_name, inc_num)


        pagination = Pagination(page=page,
                                per_page=per_page,
                                total=total_count,
                                record_name='Sentences',
                                bs_version=4,
                                alignment='center',
                                show_single_page=True)


        return render_template('text_board.html',
                               board_total=board_search,
                               user_id=user_id,
                               pagination=pagination,
                               page=page,
                               search_msg=search_msg_escaped,
                               asc1_desc0=asc1_desc0,
                               col_name=col_name,
                               sid1_count=sid1_count,
                               sid2_count=sid2_count,
                               article_title=article_title,
                               article_id=article_id,
                               sid1=sid1,
                               sid2=sid2,
                               inc_num=inc_num,
                               inc_num_none_count=inc_num_none_count,
                               inc_num_0_count=inc_num_0_count,
                               inc_num_1_count=inc_num_1_count,
                               sentence_board_type=sentence_board_type)


    # 특정 기사를 클릭한 경우
    elif search_msg is None and article_id is not None:
        print('특정 기사 클릭')
        sentence_board_type = 2

        total_count = db_helper.total_count_clicked_article(article_id, inc_num)

        inc_num_0_count = db_helper.total_count_clicked_article(article_id, '0')
        inc_num_1_count = db_helper.total_count_clicked_article(article_id, '1')
        inc_num_none_count = db_helper.total_count_clicked_article(article_id, None)

        article_title = db_helper.select_data_from_table_by_id('article_title', 'ArticleTable', article_id)


        board_clicked_article = db_helper.call_sentence_by_article_id(page, per_page, article_id, asc1_desc0, col_name, inc_num)


        pagination = Pagination(page=page,
                                per_page=per_page,
                                total=total_count,
                                record_name='Sentences',
                                bs_version=4,
                                alignment='center',
                                show_single_page=True)

        return render_template('text_board.html',
                               board_total=board_clicked_article,
                               user_id=user_id,
                               pagination=pagination,
                               page=page,
                               asc1_desc0=asc1_desc0,
                               col_name=col_name,
                               sid1_count=sid1_count,
                               sid2_count=sid2_count,
                               article_title=article_title,
                               article_id=article_id,
                               sid1=sid1,
                               sid2=sid2,
                               inc_num=inc_num,
                               inc_num_none_count=inc_num_none_count,
                               inc_num_0_count=inc_num_0_count,
                               inc_num_1_count=inc_num_1_count,
                               sentence_board_type=sentence_board_type)



    # 특정 기사에서 검색한 문장 반환
    elif search_msg is not None and article_id is not None:
        print('특정 기사 검색')
        sentence_board_type = 3

        search_msg_escaped = db_conn.escape_string(search_msg)
        total_count = db_helper.total_count_clicked_search(article_id, search_msg_escaped, inc_num)

        inc_num_0_count = db_helper.total_count_clicked_search(article_id, search_msg_escaped, '0')
        inc_num_1_count = db_helper.total_count_clicked_search(article_id, search_msg_escaped, '1')
        inc_num_none_count = db_helper.total_count_clicked_search(article_id, search_msg_escaped, None)

        article_title = db_helper.select_data_from_table_by_id('article_title', 'ArticleTable', article_id)

        board_clicked_search = db_helper.call_clicked_search(page, per_page, article_id, search_msg_escaped, asc1_desc0, col_name, inc_num)

        pagination = Pagination(page=page,
                                per_page=per_page,
                                total=total_count,
                                record_name='Sentences',
                                bs_version=4,
                                alignment='center',
                                show_single_page=True)

        return render_template('text_board.html',
                               board_total=board_clicked_search,
                               user_id=user_id,
                               pagination=pagination,
                               page=page,
                               search_msg=search_msg_escaped,
                               asc1_desc0=asc1_desc0,
                               col_name=col_name,
                               sid1_count=sid1_count,
                               sid2_count=sid2_count,
                               article_title=article_title,
                               article_id=article_id,
                               sid1=sid1,
                               sid2=sid2,
                               inc_num=inc_num,
                               inc_num_none_count=inc_num_none_count,
                               inc_num_0_count=inc_num_0_count,
                               inc_num_1_count=inc_num_1_count,
                               sentence_board_type=sentence_board_type)



    # 게시글 전체 반환
    elif search_msg is None and article_id is None:
        print('문장 전체')
        sentence_board_type = 4

        '''
        total_count = db_helper.total_count_every_sentences(inc_num)

        inc_num_0_count = db_helper.total_count_every_sentences('0')
        inc_num_1_count = db_helper.total_count_every_sentences('1')
        inc_num_none_count = db_helper.total_count_every_sentences(None)
        
        board_total = db_helper.call_every_sentence(page, per_page, asc1_desc0, col_name, inc_num)
        '''

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


        total_count = len(board_total)



        pagination = Pagination(page=page,
                                per_page=per_page,
                                total=total_count,
                                record_name='Sentences',
                                bs_version=4,
                                alignment='center',
                                show_single_page=True)


        return render_template('text_board.html',
                               board_total=board_total,
                               user_id=user_id,
                               pagination=pagination,
                               page=page,
                               asc1_desc0=asc1_desc0,
                               col_name=col_name,
                               sid1_count=sid1_count,
                               sid2_count=sid2_count,
                               inc_num=inc_num,
                               rows_category=rows_category,
                               rows_topic=rows_topic,
                               rows_act=rows_act,
                               sentence_board_type=sentence_board_type,
                               is_all_sents=1)







@app.route('/text_board', methods = ['POST', 'GET'])
#@flask_login.login_required
def text_board():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    print(request.method + '\t' + request.url)
    search_msg = request.args.get('search_msg')

    #user_id = flask_login.current_user.user_id
    user_id = 'chris'




    if request.method == 'GET':
        return reload_text_board(search_msg)



    elif request.method == 'POST':

        if request.form['ORIGINAL'] == '' or request.form['CONVERTED'] == '':
            flash('텍스트를 입력해 주세요.','alert-danger')

            id = session['sent_id']
            original_text = db_helper.select_data_from_table_by_id('sent_original', 'SentenceTable', id)

            #converted_list = NumberToWord(original_text)
            #converted_text = "\n".join(converted_list)

            page = request.args.get('page')

            #return render_template('text_edit.html', original_text = original_text, converted_text = converted_text, page = page, user_id=user_id)
            return render_template('text_edit.html', original_text=original_text, page=page,user_id=user_id)


        id = session['sent_id']

        sent_converted_count = db_helper.select_data_from_table_by_id('sent_converted_count','SentenceTable', id)
        sent_converted_count = sent_converted_count + 1
        db_helper.update_sent_converted_count(sent_converted_count, id)


        if 'ambiguity' in request.form:
            db_helper.update_sent_ambiguity(1, id)
        else:
            db_helper.update_sent_ambiguity(0, id)


        # POST method 인 경우 값을 받아오는 방식
        converted_text = request.form['CONVERTED']
        converted_text_escaped = db_conn.escape_string(converted_text)

        db_helper.update_sent_converted(converted_text_escaped, id)
        db_helper.update_sent_modified_date(id)
        db_helper.update_sent_confirm(id)


        return reload_text_board(search_msg)







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







@app.route('/<board_type>/delete', methods=['POST'])
#@flask_login.login_required
def delete(board_type):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    print(request.url)
    print(request.method)

    '''
    if board_type == 'article_board':
        # POST method 받아오는 방법
        page = request.form['page']
        article_id = request.form['article_id']

        # 해당 article_id 삭제
        db_helper.delete_by_id('ArticleTable', article_id)
        return redirect(url_for('article_board', page=page))
    '''

    #elif board_type == 'text_board':
    # POST method 받아오는 방법
    page = request.form['page']
    id = request.form['id']
    table_name = request.form['table_name']

    # 해당 id 삭제
    db_helper.delete_row_by_id(table_name, id)

    if table_name == 'act':
        return redirect(url_for('act_manager', page=page))
    else:
        return redirect(url_for('text_board', page=page))



@app.route('/text_board/create', methods = ['GET', 'POST'])
@flask_login.login_required
def text_create():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    print(request.method)

    user_id = flask_login.current_user.user_id
    page = request.args.get('page')


    if request.method == 'GET':
        return render_template('text_create.html', page = page, user_id=user_id)



    elif request.method == 'POST':
        if request.form['text_create'] == '':
            flash('텍스트를 입력해주세요.', 'alert-danger')
            return render_template('text_create.html', page = page, user_id=user_id)


        added_dict = {}

        # POST 방식으로 보낸 정보 받아오기
        text_create = request.form['text_create']
        print('created text: ' + text_create)


        largest_sent_id = db_helper.select_largest_sent_id()

        # 새로운 텍스트의 문장 번호는 현재까지 저장된 문장들 중 가장 큰 번호 +1
        added_dict['sent_id'] = largest_sent_id + 1
        added_dict['sent_original'] = text_create

        # 기사로부터 가져온 것이 아니라 새로 추가한 것이기 때문에 1 로 설정, article_id는 0으로 설정
        added_dict['sent_is_added'] = 1
        added_dict['ArticleTable_article_id'] = 0



        # 새로운 텍스트 DB에 등록
        db_helper.insert_new_text(added_dict)

        # 0번 기사의 article_sent_count 1증가
        db_helper.update_article_sent_count(+1, 0)

        return redirect(url_for('text_board', page = page, user_id=user_id, article_id=0))


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



@app.route('/export', defaults={'button_type':''})
@app.route('/export/<button_type>', methods=['GET', 'POST'])
@flask_login.login_required
def export(button_type):
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)
    user_id = flask_login.current_user.user_id

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


@app.route('/act_manager', methods=['GET'])
def act_manager():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    # 공통 코드 ==========================================
    page = request.args.get('page', type=int, default=1)
    per_page = 10

    asc1_desc0 = request.args.get('asc1_desc0')
    col_name = request.args.get('col_name')
    # ===================================================

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


    total_count = len(board_total)

    pagination = Pagination(page=page,
                            per_page=per_page,
                            total=total_count,
                            record_name='Act',
                            bs_version=4,
                            alignment='center',
                            show_single_page=True)

    return render_template('act_manager.html',
                           pagination=pagination,
                           board_total=board_total,
                           rows_act=rows_act,
                           page=page)


@app.route('/act_create', methods=['POST'])
def act_create():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)


    page = request.args.get('page')
    act = request.form['act']
    category = request.form['category']
    topic = request.form['topic']

    ######################################################################################

    return redirect(url_for('act_manager', page=page))


@app.route('/ajax_find_cat_n_topic', methods=['POST'])
def ajax_find_cat_n_topic():
    db_conn = get_db()
    db_helper = DB_Helper(db_conn)

    res = {}
    res['success'] = True

    # act_manager에서 ajax로 보낸 act값
    act = request.form['act']

    rows_act = db_helper.select_table('act')
    for row_act in rows_act:
        if row_act['act'] == act:
            category_id = row_act['category_id']
            row_category = db_helper.select_row_by_id('category', category_id)
            res['category'] = row_category['category']

            topic_id = row_act['topic_id']
            row_topic = db_helper.select_row_by_id('topic', topic_id)
            res['topic'] = row_topic['topic']

            break


    return json.dumps(res)


@app.route('/speech_create', methods=['POST'])
def speech_create():
    print('1')



# ==================================================================================================================================





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)