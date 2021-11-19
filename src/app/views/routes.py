from app import app
from app.models import db
from app.models import User
from flask import request, session, render_template, g
from sqlalchemy.exc import IntegrityError

def login_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user is None:
        return None
    if user.auth(password):
        session['user_id'] = user.id
        return user
    else:
        return None

@app.before_request
def load_user():
    if "user_id" in session:
        user_id = session["user_id"]
        g.user = User.query.get(user_id)

@app.route('/')
def search():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html', User=User)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            return render_template('login_fail.html')
        user = login_user(login, password)
        load_user()
        if user is None:
            return render_template('login_fail.html')
        else:
            return render_template('login_success.html')
@app.route('/logout')
def logout():
    try:
        del session['user_id']
        del g.user
    except KeyError or AttributeError:
        pass
    return render_template("logout.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            return render_template('msg.html', msg="Both login and password are required parameters")
        user = User(login, password)
        db.session.add(user)
        try:
            db.session.commit()
            return render_template('msg.html', msg=f"Successfully registered {user.login}")
        except IntegrityError:
            return render_template('msg.html', msg=f"User '{user.login}' already exists")
