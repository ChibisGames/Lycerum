import os, json

from flask import render_template, request, url_for, redirect, flash, session
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from webapp import app, db, MAXIMUM_QUANTITY, MAX_CONTENT_LENGTH
from webapp.models import User, Record, Files


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/posts', methods=['POST', 'GET'])
@login_required
def posts():
    if request.method == "POST":
        subject = request.form['subject']
        if subject == 'all':
            return render_template('posts.html',
                                   items=Record.query.order_by(Record.date.desc()).all()
                                   )
        return render_template('posts.html',
                               items=Record.query.filter(Record.subject == subject).order_by(Record.date.desc()).all()
                               )
    return render_template('posts.html',
                           items=Record.query.order_by(Record.date.desc()).all()
                           )


@app.route('/posts/<int:id>', methods=['POST', 'GET'])
@login_required
def posts_record(id):
    try:
        user = User.query.get(session['users'])
        record = Record.query.get(id)
        files = Files.query.filter_by(record_id=record.id).all()
    except AttributeError:
        return redirect('/posts')
    if record.user_id == session['users'] or user.admin >= 1:
        edit = True
        delete = True
    else:
        edit = False
        delete = False
    if request.method == "POST":
        if request.form['delete_btn']:
            for i in range(record.sum_of_files):
                file = Files.query.filter_by(record_id=record.id).first()
                os.remove(os.path.join('webapp', 'static', 'files', file.filename))
                db.session.delete(file)
            db.session.delete(record)
            record.users.sum_of_record -= 1
            db.session.commit()
            return redirect('/posts')
    return render_template('posts_record.html',
                           item=record,
                           edit=edit,
                           delete=delete,
                           files=files
                           )


@app.route('/posts_record/<int:id>', methods=['POST', 'GET'])
@login_required
def change_record(id):
    record = Record.query.get(id)
    files = Files.query.filter_by(record_id=record.id).all()
    total_p = 0
    total_files = len(files)
    for i in files:
        total_p += os.path.getsize(os.path.join('webapp', 'static', 'files', i.filename))
    if request.method == "POST":
        title = request.form['title']
        subject = request.form['subject']
        text = request.form['text']
        new_files = request.files.getlist('files')
        add_files = request.form['add_files']
        delete_files = request.form['output'].split()
        if len(new_files) == 1:
            if new_files[0].content_type == 'application/octet-stream':
                new_files = []
        try:
            record.title = title
            record.subject = subject
            record.text = text
            record.sum_of_files -= len(delete_files)
            for f in delete_files:
                file = Files.query.filter_by(record_id=record.id, filename=f).first()
                os.remove(os.path.join('webapp', 'static', 'files', file.filename))
                db.session.delete(file)
            db.session.commit()

            if len(add_files.split()) == 1:
                id_new_file = 0
                if files:
                    last_file = files[-1]
                    id_new_file = int(last_file.filename.split('_')[0]) + 1
                len_new_files = len(new_files)
                for i in range(len_new_files):
                    format = str(new_files[i].filename.split('.')[-1])
                    filename = str(i + id_new_file) + '_' + str(record.id) + '_' + new_files[i].filename
                    path = os.path.join('webapp', 'static', 'files', filename)

                    new_files[i].seek(0)
                    new_files[i].save(path)

                    path = os.path.join('..', 'static', 'files', filename)
                    file = Files(
                        filename=filename,
                        path_to_explorer=path,
                        format=format
                    )

                    record.record.append(file)
                record.sum_of_files += len_new_files
                db.session.commit()

            return redirect(f'/posts/{record.id}')
        except:
            return 'DATABASE creation failed'
    return render_template('change_record.html',
                           item=record,
                           files=files,
                           maximum=MAX_CONTENT_LENGTH,
                           maximum_quantity=MAXIMUM_QUANTITY,
                           total_p=total_p,
                           total_files=total_files
                           )


@app.route('/personal_account')
@login_required
def personal_account():
    user = User.query.filter(User.id == session['users']).first()
    return render_template('personal_account.html',
                           item=user
                           )


@app.route('/create_record', methods=['POST', 'GET'])
@login_required
def create_record():
    if request.method == "POST":
        title = request.form['title']
        subject = request.form['subject']
        text = request.form['text']
        files = request.files.getlist('files')
        add_files = request.form['add_files']
        if len(files) == 1:
            if files[0].content_type == 'application/octet-stream':
                files = []
        true = bool(title.split()) and (bool(text.split()) or bool(files))
        if not true:
            return redirect('/create_record')
        try:
            user = User.query.filter(User.id == session['users']).first()
            user.sum_of_record += 1
            record = Record(title=title, subject=subject, text=text)
            user.user.append(record)
            db.session.commit()
            if len(add_files.split()) == 1:
                for i in range(len(files)):
                    format = str(files[i].filename.split('.')[-1])
                    filename = str(i) + '_' + str(record.id) + '_' + files[i].filename
                    path = os.path.join('webapp', 'static', 'files', filename)

                    files[i].seek(0)
                    files[i].save(path)

                    path = os.path.join('..', 'static', 'files', filename)
                    file = Files(
                        filename=filename,
                        path_to_explorer=path,
                        format=format
                    )

                    record.sum_of_files = len(files)
                    record.record.append(file)
                db.session.commit()
            return redirect('/posts')
        except:
            return 'DATABASE creation failed'
    return render_template('create_record.html',
                           maximum=MAX_CONTENT_LENGTH,
                           maximum_quantity=MAXIMUM_QUANTITY
                           )


@app.route('/admin_console', methods=['POST', 'GET'])
@login_required
def admin_console():
    incoming = User.query.get(session['users'])
    if request.method == "POST" and incoming.admin == 2:
        user_login = request.form['user_login']
        password = request.form['password']
        admin = request.form['admin']

        fullname = request.form['fullname']
        school_class = request.form['school_class']
        birth_date = request.form['birth_date']
        if admin.isdigit():
            try:
                hash_psw = generate_password_hash(password)
                user = User(
                    user_login=user_login,
                    password=hash_psw,
                    admin=admin,
                    fullname=fullname,
                    school_class=school_class,
                    birth_date=birth_date
                )
                db.session.add(user)
                db.session.commit()
                return redirect('/')
            except Exception:
                return 'DATABASE creation failed'
        else:
            return render_template('admin_console.html')
    else:
        return render_template('admin_console.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    # Всегда существует 1-ый пользователь
    if not User.query.all():
        from werkzeug.security import generate_password_hash

        db.session.add(User(
            user_login='GlifsxevizWivkic23102005',
            password=generate_password_hash('KpsfepTvsfpiq2023'),
            admin=2,
            fullname='Чеботарев Сергей Александрович',
            school_class='11б',
            birth_date='23.10.2005'
        ))
        db.session.commit()

    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(user_login=login).first()
        if user and check_password_hash(user.password, password):
            login_user(user)

            next_page = request.args.get('next')
            session['users'] = user.id
            return redirect(next_page)
        else:
            flash("Логин и пароль не корректны")
    else:
        flash("Введите логин и пароль")
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout_page():
    logout_user()
    return redirect('/')


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)
    return response
