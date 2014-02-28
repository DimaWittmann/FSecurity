import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import os.path
from forms import NewFileForm, SignInForm, RegistrationForm, QuestionForm
from flask.ext.mail import Mail, Message
from time import time, localtime, strftime

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'security.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT= 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL= True,
    MAIL_USERNAME = 'fslabv14@gmail.com',
    MAIL_PASSWORD = 'tghmns56',
    DEFAULT_MAIL_SENDER = 'fslabv14@gmail.com'

))


mail = Mail(app)

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

LAST_REFRESH = time()
MAX_DELAY = 200
NEXT_URL = None

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    return rv


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/question', methods=['GET', 'POST'])
def question():

    form = QuestionForm(request.form)
    db = get_db()
    (question, answer)= db.cursor().execute("select question, answer from profile where profile_id = ?;", \
                           [session["id"]]).fetchone()

    if request.method == 'POST' and form.validate():
        
        if(answer == form.answer.data):
            return redirect(url_for('index'))
        flash("Answer is incorrect")

    var = {}
    var['title'] = 'FSecurity | Question' 
    var['form'] = form
    var['question'] = question
    return render_template('question.html', **var)


def is_logged():
    if session.get("admin"):
        return True

    if not session.get("sign_in"):
        return False 

    return True


def send_mail(recipient, title, text):
    message = Message(
                      title, 
                      sender='DimaWittmann@gmail.com',
                      recipients = [recipient])
    
    message.body = text
    mail.send(message)


@app.route('/', methods=['GET', 'POST'])
def index():
    var = {}
    var['title'] = 'FSecurity'

    if is_logged():
        var['title'] = 'FSecurity | {user}'.format(user=session["nickname"])
    return render_template('index.html', **var)


def create_new_file(title, text, modify=False):
    
    if is_logged():
        global LAST_REFRESH
        
        if (time() - LAST_REFRESH) > MAX_DELAY:
            LAST_REFRESH = time()
            return redirect(url_for('question'))
        LAST_REFRESH = time()

        dir_name = "Files/{user}".format(user=session["nickname"])
        file_name = "{dir}/{file}".format(dir=dir_name, file=title)
        
        db = get_db()
        count = db.cursor().execute("select count(*) from file where title = ? ;", [title]).fetchone()[0]
        if count == 0:

            db.cursor().execute('insert into file(profile_id, title, reference) values(?, ?, ?);', \
                       [session["id"], title, file_name])
            db.commit()
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            with open(file_name, 'w') as file:
                file.write(text)
                flash("{file} is created".format(file=title))
                db = get_db()
                db.cursor().execute('insert into log(profile_id, description, warning_level, data) values(?, ?, ?, ?);', \
                        [session["id"], 
                        "user create {file}".format(file=title), 0, time()])
                db.commit()
        elif modify:
            
            with open(file_name, 'w') as file:
                file.write(text)
                flash("{file} is modify".format(file=title))
                db = get_db()
                db.cursor().execute('insert into log(profile_id, description, warning_level, data) values(?, ?, ?, ?);', \
                        [session["id"], 
                        "user modify {file}".format(file=title), 0, time()])
                db.commit()
        else:
            flash("{file} is exists".format(file=title))
    else:
        flash("Please, sign in before create file")

@app.route('/create_file', methods=['GET', 'POST'])
def create_file():
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))

    global LAST_REFRESH
    if (time() - LAST_REFRESH) > MAX_DELAY:
        LAST_REFRESH = time()
        return redirect(url_for('question'))
    LAST_REFRESH = time()

    form = NewFileForm(request.form)
    if request.method == 'POST' and form.validate():
        create_new_file(form.title.data, form.content.data)
        return redirect(url_for('index'))
    
    var = {}
    var['title'] = 'FSecurity | New File'
    var['form'] = form
    return render_template('new_file.html', **var)


@app.route('/modify_file/<int:file_id>', methods=['GET', 'POST'])
def modify_file(file_id):
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))

    global LAST_REFRESH
    LAST_REFRESH = time()
    if (time() - LAST_REFRESH) > MAX_DELAY:
        
        return redirect(url_for('question'))

    form = NewFileForm(request.form)
    if request.method == 'POST' and form.validate():
        create_new_file(form.title.data, form.content.data, modify=True)

    db = get_db()
    query = db.cursor().execute("select title, reference from file where file_id = ?;", \
                       [file_id]).fetchone()
    file = open(query[1], 'r')
    content = file.read()
    form.default_title = query[0]
    form.default_content = content.replace("\n", "\\n")
    form.default_content = form.default_content.replace("\r", "\\r")
    var = {}
    var['title'] = 'FSecurity | file {title}'.format(title=query[0])
    var['form'] = form
    var['file_id'] = file_id
    return render_template('modify_file.html', **var)


@app.route('/file/<int:file_id>')
def file(file_id):
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))

    global LAST_REFRESH
    
    if (time() - LAST_REFRESH) > MAX_DELAY:
        LAST_REFRESH = time()
        return redirect(url_for('question'))
    LAST_REFRESH = time()
    db = get_db()
    query = db.cursor().execute("select title, reference from file where file_id = ?;", \
                           [file_id]).fetchone()

    file = open(query[1], 'r')
    content = file.read()
    var = {}
    var['title'] = 'FSecurity | file {file_title}'.format(file_title=query[0])
    var['file_title'] = query[0]
    var['file_content'] = content
    return render_template('file.html', **var)
        
@app.route('/delete_file/<int:file_id>')
def delete_file(file_id):
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))

    global LAST_REFRESH
    
    if (time() - LAST_REFRESH) > MAX_DELAY:
        LAST_REFRESH = time()
        return redirect(url_for('question'))
    LAST_REFRESH = time()
    db = get_db()
    query = db.cursor().execute("select file_id, title, reference from file where file_id = ?;", \
                           [file_id]).fetchone()

    os.remove(query[2])
    db.cursor().execute("DELETE FROM file WHERE file_id = ? ", (query[0],))
    db.commit()
    flash("File {file} is deleted".format(file=query[1]))
    db = get_db()
    db.cursor().execute('insert into log(profile_id, description, warning_level,data) values(?, ?, ?, ?);', \
            [session["id"], 
            "user delete {file}".format(file=query[1]), 1, time()])
    db.commit()
    return redirect(url_for('index'))


@app.route('/old_files', methods=['GET', 'POST'])
def old_files():
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))



    global LAST_REFRESH
    if (time() - LAST_REFRESH) > MAX_DELAY:   
        LAST_REFRESH = time()  
        return redirect(url_for('question'))
    LAST_REFRESH = time()
    var = {}
    var['title'] = 'FSecurity | {user} files'.format(user=session["nickname"])
    db = get_db()
    query = db.cursor().execute("select title, file_id from file where profile_id = ?  ;", \
                           [session["id"]]).fetchall()
    var['files'] = query
    return render_template('old_files.html', **var)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        count = db.execute("select count(*) from profile where login = ? ;", [form.nickname.data]).fetchone()[0]
        if (count == 0):
            db.cursor().execute('insert into profile(login, password, email, question, answer) values(?, ?, ?, ?, ?);', \
                       [form.nickname.data, form.password.data, form.email.data, form.question.data, form.answer.data])
            db.commit()
            
            title = "FSecurity registration"
            text = """
            Hello, {user}
            You are registered to FSecurity
            Your password is {password} 
            """.format(user=form.nickname.data, password=form.password.data)
            
            try:
                send_mail(form.email.data, title, text)
            except Exception, e:
                pass
            

            
            flash('Thank you for registering')
            
            db = get_db()
            db.cursor().execute('insert into log(description, warning_level, data) values(?, ?, ?);', \
            ["{user} created".format(user=form.nickname.data), 0, time()])
            db.commit()
            
            return redirect(url_for('index'))
        else:
            flash('Nickname have been captured before')
            
        
    var = {}
    var['title'] = 'FSecurity | Registration'
    var['form'] = form
    return render_template('registration.html', **var)

@app.route('/admin/logs')
def show_logs():
    if not session.get('admin'):
        return redirect(url_for('index'))

    db = get_db()
    query = db.cursor().execute("select * from log").fetchall()

    result = []
    for q in query:
        t = strftime("%b %d %Y %H:%M:%S", localtime(q[4]))
        q = (q[0], q[1], q[2], q[3], t)
        result.append(q)

    var = {}
    var['title'] = 'FSecurity | logs'
    var['query'] = result
    return render_template('log.html', **var)


@app.route('/admin/files')
def show_all_files():
    if not session.get('admin'):
        return redirect(url_for('index'))
    
    db = get_db()
    query = db.cursor().execute('''select file.title, file.file_id, profile.login
                                from file 
                                join profile
                                where profile.profile_id == file.profile_id;''').fetchall()
    var = {}
    var['title'] = 'FSecurity | All files'
    var['files'] = query
    return render_template('admin.html', **var)

@app.route('/sign_out')
def sign_out():
    flash("Good bye {user}!".format(user=session["nickname"]))
    session["sign_in"] = False
    session["id"] = None
    session["nickname"] = None
    session["admin"] = False
    return redirect(url_for("index"))


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    form = SignInForm(request.form)
    if request.method == 'POST' and form.validate():
        if (form.nickname.data == 'admin' and form.password.data == 'admin'):
            var = {}
            session["admin"] = True
            var['title'] = 'FSecurity | Admin'
            return redirect(url_for('show_all_files'))
        db = get_db()
        query = db.cursor().execute("select * from profile where login = ? and password =? ;", \
                           [form.nickname.data, form.password.data]).fetchall()
        if (len(query)==1):
            session["sign_in"] = True
            session["nickname"] = form.nickname.data
            session["id"] = query[0][0]
            flash("Hello {user}!".format(user=session["nickname"]))
            return redirect(url_for('index'))
        else:
            flash("Wrong user")
            db = get_db()
            db.cursor().execute('insert into log(profile_id, description, warning_level, data) values(?, ?, ?, ?);', \
            [None, "{user} try to enter with {password}"\
             .format(user=form.nickname.data, password=form.password.data), 2, time()])
            db.commit()
        
    var = {}
    var['title'] = 'FSecurity | Sign in'
    var['form'] = form
    return render_template('sign_in.html', **var)


    

if __name__ == '__main__':
    if not os.path.isfile(app.config['DATABASE']):
        init_db()
    
    app.run()
