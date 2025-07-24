import os
import sqlite3
from sqlite3 import Error

# PycharmProjects/myDiplomPythonProject/.venv

from flask import Flask, url_for, request, render_template, redirect, abort
from werkzeug.utils import secure_filename

from data import db_session, news_api
from data.news import News
from data.users import User
from forms.loginform import LoginForm
from forms.news import NewsForm
from forms.user import Register
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SECRET_KEY'] = 'just_secret_key'
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'zip', 'jpg', 'png']
debug = False


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', title='Не найдено')


@app.errorhandler(401)
def not_authorized(_):
    return redirect('/login')


@app.route('/')
@app.route('/index')
def index():
    params = {}
    params['user'] = 'читатель'
    params['title'] = 'приветствие'
    params['weather'] = 'Сегодня хорошая погода'
    return render_template('index.html',
                           **params)


@app.route('/about')
def about():
    return render_template('about.html',
                           title='Про нас')


@app.route('/contacts')
def contacts():
    return render_template('contacts.html',
                           title='Свяжитесь с нами')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html',
                               message='Неверный логин или пароль',
                               title='Ошибка авторизации',
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = Register()
    if form.validate_on_submit():  # тоже самое, что и request.method == 'POST'
        # если пароли не совпали
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Регистрация',
                                   message='Пароли не совпадают',
                                   form=form)

        db_sess = db_session.create_session()

        # Если пользователь с таким E-mail в базе уже есть
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Регистрация',
                                   message='Такой пользователь уже есть',
                                   form=form)
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html',
                           title='Регистрация', form=form)


@app.route('/upload', methods=['POST', 'GET'])
def file_upload():
    if request.method == 'GET':
        with open('old/upload.html', 'r', encoding='utf-8') as html:
            return html.read()
    elif request.method == 'POST':
        # print(request.files)
        if 'file' not in request.files:
            return 'Файл не был выбран!!!'

        file = request.files['file']

        if file.filename == '':
            return 'Файл не был выбран!!!'

        if file and allowed_file(file.filename):
            new_name = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_name))
            return f'Файл {new_name} успешно загружен!'
    return "Ошибка загрузки"


@app.route('/news')
@login_required
def news():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        all_news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True)).all()
    else:
        all_news = db_sess.query(News).filter(News.is_private != True).all()
    return render_template('news.html',
                           title='Новости', news=all_news)


@app.route('/newsjob', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/news')
    return render_template('newsjob.html',
                           title='Добавление новости',
                           form=form)


@app.route('/newsjob/<int:id_num>', methods=['GET', 'POST'])
@login_required
def edit_news(id_num):
    form = NewsForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(
            News.id == id_num, News.user == current_user
        ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(
            News.id == id_num, News.user == current_user
        ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/news')
        else:
            abort(404)
    return render_template('newsjob.html',
                           title='Редактирование новости',
                           form=form)


@app.route('/newsdel/<int:news_id>')
@login_required
def news_delete(news_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(
        News.id == news_id, News.user == current_user
    ).first()

    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/news')


@app.route('/adminpage', methods=['GET', 'POST'])
@login_required
def adminpanel():
    if current_user.is_authenticated and current_user.is_admin():
        db_sess = db_session.create_session()
        res = db_sess.query(News).all()
        return render_template('admin.html',
                               title='Панель администратора',
                               news=res)
    else:
        abort(404)


if __name__ == '__main__':
    db_session.global_init('db/news.sqlite')
    app.register_blueprint(news_api.blueprint)
    app.run(host='127.0.0.1', port=5000, debug=debug)
