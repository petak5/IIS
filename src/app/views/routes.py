from app import app
from app.models import db
from app.models import User, StopProposal, Stop, Operator, Vehicle, Line, LineStop, Connection
from flask import request, session, render_template, g, abort, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError
from functools import wraps
from datetime import datetime

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
@auth('admin')
def admin_stops():
    return render_template('admin_stops.html', StopProposal=StopProposal, Stop=Stop)

@app.route('/admin/stops/add', methods=['POST'])
@auth('admin')
def admin_stops_add():
    name = request.form["name"]
    stop = Stop(name)
    db.session.add(stop)
    db.session.commit()
    return redirect(g.redir)

@app.route('/admin/stops/modify', methods=['GET','POST'])
@auth('admin')
def admin_stops_modify():
    if request.method == 'GET':
        stop_id = request.args.get('id', type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('admin_stops_modify.html', stop=stop)
    if request.method == 'POST':
        stop_id = request.form.get("id", type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        name = request.form.get('name')
        stop.name = name

        db.session.add(stop)
        try:
            db.session.commit()
            flash('Modification successful', 'success')
        except:
            flash('Unknown error', 'danger')
        return redirect(g.redir)

@app.route('/admin/stops/delete', methods=['GET','POST'])
@auth('admin')
def admin_stops_delete():
    if request.method == 'GET':
        stop_id = request.args.get('id', type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('admin_stops_delete.html', stop=stop)
    if request.method == 'POST':
        stop_id = request.form.get("id", type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)

        db.session.delete(stop)
        try:
            db.session.commit()
            flash('Stop successfully deleted', 'success')
        except:
            flash('Unknown error', 'danger')
        return redirect(g.redir)

@app.route('/admin/stops/proposal_approve', methods=['POST'])
@auth('admin')
def admin_stops_proposal_approve():
    stop_proposal_id = request.form["id"]
    stop_proposal = StopProposal.query.get(stop_proposal_id)
    if stop_proposal is None:
        flash('Invalid request', 'danger')
        return redirect(g.redir)
    original_id = stop_proposal.original_id
    name = stop_proposal.name
    if original_id:
        stop = Stop.query.get(original_id)
        # Empty name means it should be deleted
        if name == "":
            db.session.delete(stop)
        else:
            stop.name = name
        db.session.delete(stop_proposal)
    else:
        stop = Stop(name)
        db.session.add(stop)
        db.session.delete(stop_proposal)
    db.session.commit()
    flash('Stop proposal approved', 'success')
    return redirect(g.redir)

@app.route('/admin/stops/proposal_decline', methods=['POST'])
@auth('admin')
def admin_stops_proposal_decline():
    stop_proposal_id = request.form["id"]
    stop_proposal = StopProposal.query.get(stop_proposal_id)
    if stop_proposal is None:
        flash('Invalid request', 'danger')
        return redirect(g.redir)
    db.session.delete(stop_proposal)
    db.session.commit()
    flash('Stop proposal declined', 'success')
    return redirect(g.redir)

@app.route('/admin/users')
@auth('admin')
def admin_users():
    return render_template('admin_users.html', User=User, Operator=Operator)

@app.route('/admin/users/add', methods=['POST'])
@auth('admin')
def admin_users_add():
    login = request.form["login"]
    password = request.form.get("password")
    role = request.form.get('role')
    operator_name = request.form.get('operator_name')
    employer_id = request.form.get('employer_id')
    if password == '':
        password = None
    user = User(login, password)
    if role == "admin":
        user.admin = True
    elif role == "operator":
        operator = Operator(operator_name)
        user.operator = operator
    elif role == "crew":
        employer = Operator.query.get(employer_id)
        user.employer = employer
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

        delete_crew = True if request.form.get('delete_crew') == 'yes' else False

        if user.is_operator():
            for employee in user.operator.employees:
                if delete_crew:
                    db.session.delete(employee)
                else:
                    employee.employer = None
                    db.session.add(employee)
        if user.operator:
            db.session.delete(user.operator)
        db.session.delete(user)
        try:
            db.session.commit()
            flash('User successfuly deleted', 'success')
        except:
            flash('Unknown error', 'danger')
        return redirect(g.redir)

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
    db.session.commit()
    flash('New operator successfuly added', 'success')
    return redirect(g.redir)

@app.route('/operator/stops_deletion_proposal', methods=['GET', 'POST'])
@auth('operator')
def operator_stops_deletion_proposal():
    if request.method == 'GET':
        stop_id = request.args.get('id', type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_stops_deletion_proposal.html', stop=stop)
    if request.method == 'POST':
        stop_id = request.form["id"]
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        # Empty name means it should be deleted
        sp = StopProposal("")
        sp.original = stop
        db.session.add(sp)
        db.session.commit()
        flash('Stop deletion proposal submitted for admin approval.', 'success')
        return redirect(g.redir)

@app.route('/operator/stops_modification_proposal', methods=['GET', 'POST'])
@auth('operator')
def operator_stops_modification_proposal():
    if request.method == 'GET':
        stop_id = request.args.get('id', type=int)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_stops_modification_proposal.html', stop=stop)
    if request.method == 'POST':
        name = request.form["name"]
        # Empty name is used to signalize deletion proposal, it is not a valid value
        if name == '':
            stop_id = request.form.get('id', type=int)
            stop = Stop.query.get(stop_id)
            if not stop:
                flash('Stop doesn\'t exist', 'danger')
                return redirect(g.redir)
            flash('Proposed stop has to have a name.', 'danger')
            return render_template('operator_stops_modification_proposal.html', stop=stop)
        sp = StopProposal(name)
        original_id = request.form.get("id")
        if original_id:
            original = Stop.query.get(original_id)
            if not original:
                flash('Stop doesn\'t exist', 'danger')
                return redirect(g.redir)
            sp.original = original
        db.session.add(sp)
        db.session.commit()
        flash('Stop modification proposal submitted for admin approval.', 'success')
        return redirect(g.redir)

@app.route('/operator/stops_proposal', methods=['GET', 'POST'])
@auth('operator')
def operator_stops_proposal():
    if request.method == 'GET':
        return render_template('operator_stops_proposal.html', Stop=Stop, StopProposal=StopProposal)
    if request.method == 'POST':
        name = request.form["name"]
        if name == '' or name is None:
            flash('Proposed stop has to have a name.', 'danger')
            return redirect(g.redir)
        sp = StopProposal(name)
        db.session.add(sp)
        db.session.commit()
        flash('Stop creation proposal submitted for admin approval.', 'success')
        return redirect(g.redir)

@app.route('/operator/stops_proposal/delete', methods=['GET', 'POST'])
@auth('operator')
def operator_stops_proposal_delete():
    if request.method == 'GET':
        sp_id = request.args.get('id', type=int)
        sp = StopProposal.query.get(sp_id)
        if not sp:
            flash('Stop proposal doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_stops_proposal_delete.html', stopProposal=sp)
    if request.method == 'POST':
        sp_id = request.form["id"]
        sp = StopProposal.query.get(sp_id)
        db.session.delete(sp)
        db.session.commit()
        flash('Stop proposal deleted.', 'success')
        return redirect(g.redir)

@app.route('/operator/connections', methods=['GET'])
@auth('operator')
def operator_connections():
    if not g.operator:
        flash('Only operator can view this page', 'danger')
        return render_template('placeholder.html')
    return render_template('operator_connections.html', operator=g.operator)

@app.route('/operator/connections/add', methods=['POST'])
@auth('operator')
def operator_connections_add():
    line_id = request.form.get("line", type=int)
    line = Line.query.get(line_id)
    departure_date = request.form.get("date")
    departure_time = request.form.get("time")
    date = datetime.strptime(departure_date, "%Y-%m-%d")
    time = datetime.strptime(departure_time, "%H:%M")
    dt = datetime.combine(date, time.time())
    vehicle_id = request.form.get("vehicle", type=int)
    vehicle = Vehicle.query.get(vehicle_id)
    connection = Connection(dt)
    connection.line = line
    connection.vehicle = vehicle
    db.session.add(connection)
    db.session.commit()
    flash('New connection successfully added.', 'success')
    return redirect(g.redir)

@app.route('/operator/lines', methods=['GET'])
@auth('operator')
def operator_lines():
    if not g.operator:
        flash('Only operator can view this page', 'danger')
        return render_template('placeholder.html')
    return render_template('operator_lines.html', operator=g.operator)

@app.route('/operator/lines/add', methods=['POST'])
@auth('operator')
def operator_lines_add():
    line_name = request.form.get("name")
    line = Line(line_name, g.operator)
    db.session.add(line)
    db.session.commit()
    flash('New line successfully added.', 'success')
    return redirect(g.redir)

@app.route('/operator/lines/delete', methods=['GET', 'POST'])
@auth('operator')
def operator_lines_delete():
    if request.method == 'GET':
        line_id = request.args.get("id", type=int)
        line = Line.query.get(line_id)
        if not line:
            flash('Line doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_lines_delete.html', line=line)
    elif request.method == 'POST':
        line_id = request.form.get("id", type=int)
        line = Line.query.get(line_id)
        if not line:
            flash('Line doesn\'t exist', 'danger')
            return redirect(g.redir)
        db.session.delete(line)
        db.session.commit()
        flash('Line successfully removed.', 'success')
        return redirect(g.redir)

@app.route('/operator/lines/stops', methods=['GET', 'POST'])
@auth('operator')
def operator_lines_stops():
    if not g.operator:
        flash('Only operator can view this page', 'danger')
        return render_template('placeholder.html')
    if request.method == 'GET':
        line_id = request.args.get("line_id", type=int)
        line = Line.query.get(line_id)
        if not line:
            flash('Line doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_lines_stops.html', Stop=Stop, line=line)
    elif request.method == 'POST':
        line_id = request.form.get("line_id", type=int)
        stop_id = request.form.get("stop", type=int)
        time_delta = request.form.get("time_delta", type=int)
        if not line_id:
            flash('Line ID doesn\'t exist', 'danger')
            return redirect(g.redir)
        line = Line.query.get(line_id)
        if not line:
            flash('Line doesn\'t exist', 'danger')
            return redirect(g.redir)
        stop = Stop.query.get(stop_id)
        if not stop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        if time_delta is None:
            time_delta = 0
        ls = LineStop(len(line.stops) + 1)
        ls.line = line
        ls.stop = stop
        ls.time_delta = time_delta
        db.session.add(ls)
        db.session.commit()
        flash('New stop successfully added.', 'success')
        return redirect(g.redir)

@app.route('/operator/vehicles', methods=['GET'])
@auth('operator')
def operator_vehicles():
    if not g.operator:
        flash('Only operator can view this page', 'danger')
        return render_template('placeholder.html')
    return render_template('operator_vehicles.html', operator=g.user.operator)

@app.route('/operator/vehicles/add', methods=['POST'])
@auth('operator')
def operator_vehicles_add():
    description = request.form.get("description")
    if not description:
        description = ''
    seats = request.form.get("seats", type=int)
    if not seats:
        flash('You have to specify number of seats', 'danger')
        return redirect(g.redir)
    vehicle = Vehicle(g.operator)
    vehicle.description = description
    vehicle.num_seats = seats
    db.session.add(vehicle)
    db.session.commit()
    flash('New vehicle successfully added.', 'success')
    return redirect(g.redir)

@app.route('/operator/vehicle/remove', methods=['GET', 'POST'])
@auth('operator')
def operator_vehicles_remove():
    if request.method == 'GET':
        vehicle_id = request.args.get("id", type=int)
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            flash('Vehicle doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_vehicles_remove.html', vehicle=vehicle)
    elif request.method == 'POST':
        vehicle_id = request.form.get("id", type=int)
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            flash('Vehicle doesn\'t exist', 'danger')
            return redirect(g.redir)
        db.session.delete(vehicle)
        db.session.commit()
        flash('Vehicle successfully removed.', 'success')
        return redirect(g.redir)

@app.route('/operator/crew', methods=['GET'])
@auth('operator')
def operator_crew():
    if not g.user.operator:
        flash('Only operator can view this page', 'danger')
        return render_template('placeholder.html')
    return render_template('operator_crew.html', User=User, operator=g.user.operator)

@app.route('/operator/crew/add', methods=['POST'])
@auth('operator')
def operator_crew_add():
    login = request.form["login"]
    password = request.form['password']
    employer_id = g.operator.id
    if password == '':
        password = None
    user = User(login, password)
    user.employer = g.operator
    db.session.add(user)
    try:
        db.session.commit()
        flash(f'Crew {login} successfully added.', 'success')
        return redirect(g.redir)
    except IntegrityError:
        flash(f'Crew {login} already exists.', 'danger')
        return redirect(g.redir)
    flash('Unknown error', 'danger')
    return redirect(g.redir)

@app.route('/operator/crew/fire', methods=['GET', 'POST'])
@auth('operator')
def operator_crew_fire():
    if request.method == 'GET':
        user_id = request.args.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_crew_fire.html', user=user)
    elif request.method == 'POST':
        user_id = request.form.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        user.employer = None
        db.session.commit()
        flash('User successfully fired.', 'success')
        return redirect(g.redir)

@app.route('/operator/crew/delete', methods=['GET', 'POST'])
@auth('operator')
def operator_crew_delete():
    if request.method == 'GET':
        user_id = request.args.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_crew_delete.html', user=user)
    elif request.method == 'POST':
        user_id = request.form.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        db.session.delete(user)
        db.session.commit()
        flash('User successfully deleted.', 'success')
        return redirect(g.redir)

@app.route('/operator/transfer', methods=['GET', 'POST'])
@auth('operator')
def operator_transfer():
    if request.method == 'GET':
        user_id = request.args.get("id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_transfer.html', User=User, user=user)
    elif request.method == 'POST':
        user_id = request.form.get("user_id", type=int)
        user = User.query.get(user_id)
        if not user:
            flash('User doesn\'t exist', 'danger')
            return redirect(g.redir)
        g.user.employer = g.operator
        g.operator.manager = user
        user.employer = None
        db.session.commit()
        flash('Operator ownership successfully transferred.', 'success')
        return redirect(g.redir)

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
            flash(f"Successfully registered as {user.login}, you may now login.", 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            flash(f"Login {user.login} is already taken.", 'danger')
            return redirect(url_for('register'))
        flash("Unknown error.", 'danger')
        return redirect(url_for('register'))
