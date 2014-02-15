import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import os.path
from forms import NewFileForm, SignInForm, RegistrationForm

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'security.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
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

def is_logged():
    return session["sign_in"]

@app.route('/', methods=['GET', 'POST'])
def index():
    var = {}
    var['title'] = 'FSecurity'
    if hasattr(session, "sign_in"):
        if session["sign_in"]:
            var['title'] = 'FSecurity | {user}'.format(user=session["nickname"])

        
    return render_template('index.html', **var)

def create_new_file(title, text, modify=False):
    
    if is_logged():
        
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
        elif modify:
            
            with open(file_name, 'w') as file:
                file.write(text)
                flash("{file} is modify".format(file=title))
        else:
            flash("{file} is exists".format(file=title))
    else:
        flash("Please, sign in before create file")

@app.route('/create_file', methods=['GET', 'POST'])
def create_file():
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))
    
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


    form = NewFileForm(request.form)
    if request.method == 'POST' and form.validate():
        create_new_file(form.title.data, form.content.data, modify=True)

    db = get_db()
    query = db.cursor().execute("select title, reference from file where profile_id = ? and file_id = ?;", \
                       [session["id"], file_id]).fetchone()
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

    db = get_db()
    query = db.cursor().execute("select title, reference from file where profile_id = ? and file_id = ?;", \
                           [session["id"], file_id]).fetchone()

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

    db = get_db()
    query = db.cursor().execute("select file_id, title, reference from file where profile_id = ? and file_id = ?;", \
                           [session["id"], file_id]).fetchone()

    os.remove(query[2])
    db.cursor().execute("DELETE FROM file WHERE file_id = ? ", (query[0],))
    db.commit()
    flash("File {file} is deleted".format(file=query[1]))
    return redirect(url_for('index'))


@app.route('/old_files', methods=['GET', 'POST'])
def old_files():
    if not is_logged():
        flash("Please, sign in")
        return redirect(url_for('index'))
    
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
            db.cursor().execute('insert into profile(login, password) values(?, ?);', \
                       [form.nickname.data, form.password.data])
            db.commit()
            flash('Thank you for registering')
            return redirect(url_for('index'))
        else:
            flash('Nickname have been captured before')
            
        
    var = {}
    var['title'] = 'FSecurity | Registration'
    var['form'] = form
    return render_template('registration.html', **var)


@app.route('/sign_out')
def sign_out():
    flash("Good bye {user}!".format(user=session["nickname"]))
    session["sign_in"] = False
    session["id"] = None
    session["nickname"] = None
    return redirect(url_for("index"))


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    form = SignInForm(request.form)
    if request.method == 'POST' and form.validate():
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
        
    var = {}
    var['title'] = 'FSecurity | Sign in'
    var['form'] = form
    return render_template('sign_in.html', **var)


if __name__ == '__main__':
    if not os.path.isfile(app.config['DATABASE']):
        init_db()
    
    app.run()
