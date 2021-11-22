from app import app
from app.models import db
from app.models import User, StopProposal, Stop
from flask import request, session, render_template, g, abort, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError
from functools import wraps

def login_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user is None:
        return None
    if user.auth(password):
        session['user_id'] = user.id
        return user
    else:
        return None

def is_auth(privilege):
    if g.user == None:
        return False
    elif g.user.is_admin():
        return True
    elif privilege == 'admin' and not g.user.is_admin():
        return False
    elif privilege == 'operator' and not g.user.is_operator():
        return False
    elif privilege == 'crew' and not g.user.is_crew():
        return False
    elif privilege == 'user':
        return True
    else:
        return True

def auth(privilege):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if privilege == 'user' and g.user == None:
                flash("You have to be logged in to access that page", 'danger')
                return redirect(url_for('login', redir=request.url)) # TODO redirect in login afterwards
            if g.user == None:
                if privilege == 'admin':
                    flash("You have to be logged in as an admin to access that page", 'danger')
                if privilege == 'operator':
                    flash("You have to be logged in as an transport operator to access that page", 'danger')
                if privilege == 'crew':
                    flash("You have to be logged in as a member of crew to access that page", 'danger')
                return redirect(url_for('login', redir=request.url)) # TODO redirect in login afterwards
            if g.user.is_admin():
                return func(*args, **kwargs)
            if privilege == 'admin' and not g.user.is_admin():
                flash('Insufficient privileges. You need to be an admin to access that page.', 'danger')
                return redirect(g.redir)
            if privilege == 'operator' and not g.user.is_operator():
                flash('Insufficient privileges. You need to be an operator to access that page.', 'danger')
                return redirect(g.redir)
            if privilege == 'crew' and not g.user.is_crew():
                flash('Insufficient privileges. You need to be crew to access that page.', 'danger')
                return redirect(g.redir)
            return func(*args, **kwargs)
        return inner
    return decorator

@app.before_request
def load_user():
    g.is_auth = is_auth
    g.user = None
    g.operator = None
    if "user_id" in session:
        user_id = session["user_id"]
        g.user = User.query.get(user_id)

    g.redir = request.form.get('redir')
    if not g.redir:
        g.redir = request.args.get('redir')
    if not g.redir:
        g.redir = url_for('index')

    if "admin_operator_id" in session:
        g.operator = Operator.get(int(session['admin_operator_id']))
        if g.operator == None:
            del session['admin_operator_id']
    if g.user:
        g.operator = g.user.operator


@app.route('/admin/stops')
def admin_stops():
    return render_template('admin_stops.html', StopProposal=StopProposal, Stop=Stop)

@app.route('/admin/stops/approve', methods=['POST'])
@auth('admin')
def admin_stops_approve():
    stop_proposal_id = request.form["id"]
    stop_proposal = StopProposal.query.get(stop_proposal_id)
    if stop_proposal is None:
        flash('Invalid request', 'danger')
        return redirect(g.redir)
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
    flash('Stop approved', 'success')
    return redirect(g.redir)

@app.route('/admin/users')
@auth('admin')
def admin_users():
    return render_template('admin_users.html', User=User)

@app.route('/admin/users/add', methods=['POST'])
@auth('admin')
def admin_users_add():
    login = request.form["login"]
    password = request.form.get("password")
    if password == '':
        password = None
    user = User(login, password)
    user.admin = True if request.form.get("admin") == 'yes' else False

    operator_id = request.form.get('operator_id')
    if operator_id:
        user.operator_id = operator_id
    employer_id = request.form.get('operator_id')
    if employer_id:
        user.employer_id = employer_id
    db.session.add(user)
    try:
        db.session.commit()
        flash(f'User {login} successfully added.', 'success')
        return redirect(g.redir)
    except IntegrityError:
        flash(f'User {login} already exists.', 'danger')
        return redirect(g.redir)
    flash('Unknown error', 'danger')
    return redirect(g.redir)

@app.route('/admin/users/modify', methods=['GET','POST'])
@auth('admin')
def admin_users_modify():
    if request.method == 'GET':
        user_id = request.args.get('id', type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('admin_users_modify.html', user=user)
    if request.method == 'POST':
        user_id = request.form.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)


        user.admin = request.form.get('admin') == 'yes'
        password = request.form.get('password')
        if password != None and password != '':
            user.password = password
        login = request.form.get('login')
        if login != None and login != '':
            user.login = login
        if request.form.get('disable_login') == 'yes':
            user.password = None
        operator_id = request.form.get('operator_id')
        if operator_id:
            user.operator_id = operator_id
        employer_id = request.form.get('employer_id')
        if employer_id:
            user.employer_id = employer_id
        db.session.add(user)
        try:
            db.session.commit()
            flash('Modification successful', 'success')
        except:
            flash('Unknown error', 'danger')
        return redirect(g.redir)

@app.route('/admin/users/delete', methods=['GET','POST'])
@auth('admin')
def admin_users_delete():
    if request.method == 'GET':
        user_id = request.args.get('id', type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('admin_users_delete.html', user=user)
    if request.method == 'POST':
        user_id = request.form.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)

        delete_crew =  True if request.args.get('delete_crew') == 'yes' else False

        if user.is_operator():
            for employee in employees:
                if delete_crew:
                    db.session.delete(employee)
                else:
                    employee.employer = None
                    db.session.add(employee)
        db.session.delete(user)
        try:
            db.session.commit()
            flash('User successfuly deleted', 'success')
        except:
            flash('Unknown error', 'danger')
        return redirect(g.redir)

@app.route('/admin/operators')
@auth('admin')
def admin_operators():
    return render_template('admin_operators.html', User=User)

@app.route('/admin/operators/pick', methods=['GET', 'POST'])
@auth('admin')
def admin_operators_pick():
    if request.method == 'GET':
        return render_template('admin_operators_pick.html')
    if request.method == 'POST':
        operator_id = request.form.get('id', type=int)
        if operator_id:
            session['admin_operator_id'] = operator_id
        return redirect(g.redir)

@app.route('/admin/operators/add', methods=['POST'])
@auth('admin')
def admin_operators_add(): # TODO error handle
    name = request.form["name"]
    login = request.form["login"]
    password = request.form.get("password")
    operator = Operator(name)
    user = User.query.filter_by(login=login).first()
    if not user:
        user = User(login, password)
    user.operator = operator
    db.session.add(operator)
    db.session.add(user)
    db.session_commit()
    flash('New operator successfuly added', 'success')
    return redirect(g.redir)

@app.route('/operator/propose_stop', methods=['GET', 'POST'])
@auth('operator')
def operator_propose_stop():
    if request.method == 'GET':
        return render_template('operator_propose_stop.html', Stop=Stop)
    if request.method == 'POST':
        name = request.form["name"]
        sp = StopProposal(name)
        original_id = request.form.get("original_id")
        if original_id:
            original = Stops.query.get(original_id)
            if not original:
                flash('Stop doesn\'t exist', 'danger')
                return redirect(g.redir)
            sp.original = original
        db.session.add(sp)
        db.session.commit()
        if original_id:
            flash('Stop modification proposal submitted for admin approval.', 'success')
        else:
            flash('Stop creation proposal submitted for admin approval.', 'success')
        return redirect(g.redir)

@app.route('/operator/connections', methods=['GET', 'POST'])
@auth('operator')
def operator_connections(): # TODO implement
    return render_template('placeholder.html')

@app.route('/operator/vehicles', methods=['GET', 'POST'])
@auth('operator')
def operator_vehicles(): # TODO implement
    return render_template('placeholder.html')

@app.route('/operator/crew', methods=['GET', 'POST'])
@auth('operator')
def operator_crew(): # TODO implement
    return render_template('placeholder.html')

@app.route('/crew/tickets', methods=['GET', 'POST'])
@auth('crew')
def crew_tickets(): # TODO implement
    return render_template('placeholder.html')

@app.route('/crew/positions', methods=['GET', 'POST'])
@auth('crew')
def crew_positions(): # TODO implement
    return render_template('placeholder.html')

@app.route('/user/reserve', methods=['GET', 'POST'])
@auth('user')
def user_reserve(): # TODO implement
    return render_template('placeholder.html')

@app.route('/user/tickets', methods=['GET', 'POST'])
@auth('user')
def user_position(): # TODO implement
    return render_template('placeholder.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            flash("Incorrect login or password.", 'danger')
            return redirect(url_for('login'))
        user = login_user(login, password)
        load_user()
        if user is None:
            flash("Incorrect login or password.", 'danger')
            return redirect(url_for('login'))
        else:
            flash("You have successfully logged in.", 'success')
            if g.redir:
                return redirect(g.redir)
            if g.user.is_admin():
                return redirect(url_for('admin'))
            return redirect(url_for('index'))

@app.route('/logout')
def logout():
    try:
        del session['user_id']
        del g.user
        del session['admin_operator_id']
        del g.operator_id
    except KeyError or AttributeError:
        pass
    flash("You have been logged out", 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            flash("Both login and password are required parameters.", 'danger')
            redirect(url_for('register'))
        user = User(login, password)
        if login == 'admin': # TODO only to simplify testing, remove later
            user.admin = True
        db.session.add(user)
        try:
            db.session.commit()
            flash(f"Succesfully registered as {user.login}, you may now login.", 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            flash(f"Login {user.login} is already taken.", 'danger')
            return redirect(url_for('register'))
        flash("Unknown error.", 'danger')
        return redirect(url_for('register'))
