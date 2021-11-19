from app import app
from app.models import db
from app.models import User, StopProposal, Stop
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
    return render_template('admin.html', User=User, StopProposal=StopProposal, Stop=Stop)

@app.route('/admin/approve_stop', methods=['POST'])
def admin_approve_stop():
    stop_proposal_id = request.form.get("id")
    if not stop_proposal_id:
        return render_template("msg.html", msg="id parameter is required") # TODO
    stop_proposal = StopProposal.query.get(stop_proposal_id)
    original_id = stop_proposal.original_id
    name = stop_proposal.name
    if original_id:
        stop = Stop.query.get(original_id)
        stop.name = name
        db.session.delete(stop_proposal)
    else:
        stop = Stop(name)
        db.session.add(stop)
        db.session.delete(stop_proposal)
    db.session.commit()
    return render_template("msg.html", msg="Stop approved")

@app.route('/admin/add_operator', methods=['POST'])
def add_operator():
    if not g.user.is_admin():
        return "Access denied", 403
    name = request.form.get("name")
    user_id = request.form.get("user_id")
    if not name or not user_id:
        return "Invalid args", 400
    operator = Operator(name)
    operator.user_id = user_id
    db.session.add(operator)
    db.session_commit()
    return "Operator Added"

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    if not g.user.is_admin():
        return "Access denied", 403
    login = request.form.get("login")
    password = request.form.get("password")
    if not login or not password:
        return "Invalid args", 400
    user = User.query.filter_by(login=login).first()
    if not login:
        return "User doesn't exist", 400
    user.password = password
    db.session.commit()
    return "Password changed"

@app.route('/operator/propose_stop', methods=['POST'])
def propose_stop():
    original_id = request.form.get("original_id")
    name = request.form.get("name")
    if not name:
        return "Invalid args", 400
    if original_id:
        original = Stops.query.get(original_id)
        if not original:
            return "Stop doesn't exist", 400
        sp = StopProposal(name, original)
    else:
        sp = StopProposal(name)
    db.session.add(sp)
    db.session.commit()
    return render_template('msg.html', msg="Success")

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
