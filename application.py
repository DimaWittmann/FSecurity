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
    return rv.cursor()


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


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NewFileForm(request.form)
    if request.method == 'POST' and form.validate():
        file = open(form.title.data, 'w+')
        file.write(form.content.data)
        flash("new file created")
    var = {}
    var['title'] = 'FSecurity'
    var['form'] = form
    return render_template('index.html', **var)

@app.route('/create_file', methods=['GET', 'POST'])
def create_file():
    pass

@app.route('/old_files', methods=['GET', 'POST'])
def old_files():
    pass


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        count = db.execute("select count(*) form profile where login = ? ;", [form.nickname.data]).fetchone()[0]
        if (count == 0):
            db.execute('insert into profile(login, password) values(?, ?);', \
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
    return redirect(url_for("index"))


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    form = SignInForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        count = db.execute("select count(*) from profile where login = ? and password =? ;", \
                           [form.nickname.data, form.password.data]).fetchone()[0]
        if (count == 1):
            session["sign_in"] = True
            session["nickname"] = form.nickname.data
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
