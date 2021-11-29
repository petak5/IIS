from app import app
from app.models import db
from app.models import User, StopProposal, Stop, Operator, Vehicle, Line, LineStop, Connection, Ticket
from flask import request, session, render_template, g, abort, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError
from functools import wraps
from datetime import datetime, timedelta

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
        g.operator = Operator.query.get(int(session['admin_operator_id']))
        if g.operator == None:
            del session['admin_operator_id']
    if g.user:
        if g.user.is_operator():
            g.operator = g.user.operator
        elif g.user.is_crew():
            g.operator = g.user.employer

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
        return render_template('admin_operators_pick.html', Operator=Operator, operator=g.operator)
    if request.method == 'POST':
        operator_id = request.form.get('operator', type=int)
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
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
    return render_template('operator_connections.html', Connection=Connection, operator=g.operator)

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

@app.route('/operator/connections/stops', methods=['GET', 'POST'])
@auth('operator')
def operator_connections_stops():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
    if request.method == 'GET':
        connection_id = request.args.get("connection_id", type=int)
        connection = Connection.query.get(connection_id)
        if not connection:
            flash('Connection doesn\'t exist', 'danger')
            return redirect(g.redir)
        line = connection.line
        stops = []
        dt = connection.start_time
        for ls in LineStop.query.filter_by(line=line).order_by(LineStop.position):
            stop = {}
            stop['name'] = ls.stop.name
            stop['position'] = ls.position
            dt += timedelta(minutes=ls.time_delta)
            stop['time'] = dt
            stops.append(stop)
        return render_template('operator_connection_stops.html', connection=connection, stops=stops)
    elif request.method == 'POST':
        connection_id = request.form.get("connection_id", type=int)
        connection = Connection.query.get(connection_id)
        if not connection:
            flash('Connection doesn\'t exist', 'danger')
            return redirect(g.redir)

        db.session.commit()
        flash('New stop successfully added.', 'success')
        return redirect(g.redir)

@app.route('/operator/connections/delete', methods=['GET', 'POST'])
@auth('operator')
def operator_connections_delete():
    if request.method == 'GET':
        connection_id = request.args.get("id", type=int)
        connection = Connection.query.get(connection_id)
        if not connection:
            flash('Connection doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_connections_delete.html', connection=connection)
    elif request.method == 'POST':
        connection_id = request.form.get("id", type=int)
        connection = Connection.query.get(connection_id)
        if not connection:
            flash('Connection doesn\'t exist', 'danger')
            return redirect(g.redir)
        for ticket in connection.tickets:
            db.session.delete(ticket)
        db.session.delete(connection)
        db.session.commit()
        flash('Connection successfully deleted.', 'success')
        return redirect(g.redir)

@app.route('/operator/lines', methods=['GET'])
@auth('operator')
def operator_lines():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
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
        for connection in line.connections:
            db.session.delete(connection)
        for lineStop in line.stops:
            db.session.delete(lineStop)
        db.session.delete(line)
        db.session.commit()
        flash('Line successfully deleted.', 'success')
        return redirect(g.redir)

@app.route('/operator/lines/stops', methods=['GET', 'POST'])
@auth('operator')
def operator_lines_stops():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
    if request.method == 'GET':
        line_id = request.args.get("line_id", type=int)
        line = Line.query.get(line_id)
        if not line:
            flash('Line doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_lines_stops.html', Stop=Stop, LineStop=LineStop, line=line)
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

@app.route('/operator/lines/stops/reorder', methods=['GET'])
@auth('operator')
def operator_lines_stops_reorder():
    direction = request.args.get("direction")
    if direction not in ["up", "down"]:
        direction = "up"
    stop_id = request.args.get("stop_id", type=int)
    stop = LineStop.query.get(stop_id)
    if not stop:
        flash('Stop doesn\'t exist', 'danger')
        return redirect(g.redir)
    line = stop.line
    if direction == "up":
        stop.position -= 1
        for ls in line.stops:
            if ls.id == stop.id:
                continue
            if ls.position == stop.position:
                ls.position += 1
    else:
        stop.position += 1
        for ls in line.stops:
            if ls.id == stop.id:
                continue
            if ls.position == stop.position:
                ls.position -= 1

    db.session.commit()
    flash('Stop successfully moved.', 'success')
    return redirect(g.redir)

@app.route('/operator/lines/stops/remove', methods=['GET', 'POST'])
@auth('operator')
def operator_lines_stops_remove():
    if request.method == 'GET':
        stop_id = request.args.get("stop_id", type=int)
        lineStop = LineStop.query.get(stop_id)
        if not lineStop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('operator_lines_stops_remove.html', lineStop=lineStop)
    elif request.method == 'POST':
        stop_id = request.form.get("stop_id", type=int)
        lineStop = LineStop.query.get(stop_id)
        if not lineStop:
            flash('Stop doesn\'t exist', 'danger')
            return redirect(g.redir)
        line = lineStop.line
        db.session.delete(lineStop)
        # Update stop positions
        counter = 1
        for ls in line.stops:
            ls.position = counter
            counter += 1
        db.session.commit()
        flash('Stop successfully removed.', 'success')
        return redirect(g.redir)

@app.route('/operator/vehicles', methods=['GET'])
@auth('operator')
def operator_vehicles():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
    return render_template('operator_vehicles.html', operator=g.operator)

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
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only operator can view that page', 'danger')
            return redirect(g.redir)
    return render_template('operator_crew.html', User=User, operator=g.operator)

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

@app.route('/crew/tickets')
@auth('crew')
def crew_tickets():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only crew can view that page', 'danger')
            return redirect(g.redir)
    return render_template('crew_tickets.html', Connection=Connection, operator=g.operator, Ticket=Ticket)

@app.route('/crew/tickets/specific')
@auth('crew')
def crew_tickets_specific():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only crew can view that page', 'danger')
            return redirect(g.redir)
    connection_id = request.args.get('connection_id', type=int)
    connection = Connection.query.get(connection_id)
    if not connection:
        flash('No such connection', 'danger')
        return redirect(g.redir)
    return render_template('crew_tickets_specific.html', Ticket=Ticket, connection=connection, operator=g.operator)

@app.route('/crew/tickets/issue', methods=['POST'])
@auth('crew')
def crew_tickets_issue():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only crew can view that page', 'danger')
            return redirect(g.redir)
    ticket_id = request.form.get('id', type=int)
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash('No such ticket', 'danger')
        return redirect(g.redir)
    flash("Pretend you just printed out a ticket successfuly", 'success')
    return redirect(g.redir)

@app.route('/crew/tickets/confirm', methods=['POST'])
@auth('crew')
def crew_tickets_confirm():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only crew can view that page', 'danger')
            return redirect(g.redir)
    ticket_id = request.form.get('id', type=int)
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash('No such ticket', 'danger')
        return redirect(g.redir)
    ticket.confirmed = True
    db.session.add(ticket)
    db.session.commit()
    flash('Ticket reservation confirmed', 'success')
    return redirect(g.redir)

@app.route('/crew/positions')
@auth('crew')
def crew_positions():
    if not g.operator:
        if g.user.is_admin():
            return redirect(url_for('admin_operators_pick', redir=request.url))
        else:
            flash('Only crew can view that page', 'danger')
            return redirect(g.redir)
    return render_template('crew_positions.html', Vehicle=Vehicle)

@app.route('/crew/positions/set', methods=['GET', 'POST'])
@auth('crew')
def crew_positions_set():
    if request.method == 'GET':
        vehicle_id = request.args.get('id')
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            flash('Vehicle doesn\'t exist', 'danger')
            return redirect(g.redir)
        return render_template('crew_positions_set.html', vehicle=vehicle, Stop=Stop)
    elif request.method == 'POST':
        vehicle_id = request.form.get('id', type=int)
        if g.user.is_admin():
            vehicle = Vehicle.query.get(vehicle_id)
        else:
            vehicle = Vehicle.query.filter_by(operator=g.operator, id=vehicle_id).first()
        stop_name = request.form.get('position')
        stop = Stop.query.filter_by(name=stop_name).first()
        if not stop or not vehicle:
            flash('Invalid request', 'danger')
            return redirect(g.redir)
        vehicle.last_known_stop = stop
        db.session.add(vehicle)
        db.session.commit()
        flash('Stop changed successfuly', 'success')
        return redirect(g.redir)

@app.route('/crew/positions/unset')
@auth('crew')
def crew_positions_unset():
    vehicle_id = request.args.get('id', type=int)
    if g.user.is_admin():
        vehicle = Vehicle.query.get(vehicle_id)
    else:
        vehicle = Vehicle.query.filter_by(operator=g.operator, id=vehicle_id).first()
    vehicle.last_known_stop = None
    db.session.add(vehicle)
    db.session.commit()
    flash('Position unset', 'success')
    return redirect(g.redir)

@app.route('/ticket_reserve', methods=['POST'])
def ticket_reserve():
    connection = Connection.query.get(request.form.get('connection', type=int))
    num_seats = request.form.get('seats', type=int)
    from_ = request.form.get('from', type=int)
    to = request.form.get('to', type=int)
    if not connection or from_ == None or to == None or num_seats <= 0:
        flash('Invalid request', 'danger')
        return redirect(g.redir)
    if not g.user:
        login = request.form.get('login')
        password = request.form.get('password')
        if login == None or login == '' or password == None or password == '':
            flash('Invalid request', 'danger')
            return redirect(g.redir)
        user = User(login, password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            flash(f"Login {user.login} is already taken.", 'danger')
            return redirect(g.redir)
        except:
            flash("Unknown error", 'danger')
            return redirect(g.redir)
    else:
        user = g.user

    if connection.get_free_seats(from_, to) < num_seats:
        flash('Not enough free seats', 'danger')
        return redirect(g.redir)
    ticket = Ticket(user)
    ticket.connection = connection
    ticket.num_seats = num_seats
    ticket.from_pos = from_
    ticket.to_pos = to
    db.session.add(ticket)
    db.session.commit()

    if g.user:
        flash('Ticket reserved successfuly', 'success')
        return redirect(url_for('user_tickets'))
    else:
        flash('Ticket reserved and account created, you may login now', 'success')
        return redirect(url_for('login', redir=url_for('user_tickets')))

@app.route('/user/tickets', methods=['GET', 'POST'])
@auth('user')
def user_tickets():
    return render_template('user_tickets.html', user=g.user)

@app.route('/')
def index():
    return render_template('index.html', Stop=Stop)

@app.route('/search')
def search():
    results = []
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    dt = request.args.get('dt', type=int) # show only connections leaving later than this
    if dt:
        dt = datetime.fromtimestamp(dt)
    else:
        dt = datetime.now()

    from_ = Stop.query.filter_by(name=from_str).first()
    to = Stop.query.filter_by(name=to_str).first()
    # TODO fuzzy match
    if not from_:
        flash(f"No such stop '{from_str}'", 'danger')
        return redirect(g.redir)
    if not to:
        flash(f"No such stop '{to_str}'", 'danger')
        return redirect(g.redir)
    # TODO error check
    for from_ls in from_.lines:
        pos = from_ls.position
        line = from_ls.line
        stops = LineStop.query.filter_by(line=line).order_by(LineStop.position)
        to_ls = stops.filter(LineStop.position > pos).filter_by(stop=to).first()
        if not to_ls:
            continue
        operator = line.operator
        start_delta = timedelta(minutes=sum(ls.time_delta for ls in stops.filter(LineStop.position <= pos)))
        duration = timedelta(minutes=sum(ls.time_delta for ls in stops.filter(LineStop.position > pos).filter(LineStop.position <= to_ls.position)))
        end_delta = start_delta+duration

        # TODO time limit and ordering and stuff
        for connection in line.connections:
            rd = {}
            rd['connection'] = connection
            rd['line'] = line
            rd['operator'] = operator
            rd['duration'] = duration
            rd['vehicle'] = connection.vehicle
            rd['start'] = connection.start_time + start_delta
            if rd['start'] < dt:
                continue
            rd['end'] = connection.start_time + end_delta
            rd['free_seats'] = connection.get_free_seats(pos, to_ls.position)
            rd['from_pos'] = pos
            rd['to_pos'] = to_ls.position
            results.append(rd)
    results.sort(key=lambda r: r['start'])
    return render_template('search.html', results=results, from_=from_, to=to)

@app.route('/connection_detail')
def connection_detail():
    connection_id = request.args.get('id')
    connection = Connection.query.get(connection_id)
    if not connection:
        flash('Invalid connection', 'danger')
        return redirect(g.redir)
    from_pos = request.args.get('from', type=int)
    to_pos = request.args.get('to', type=int)
    if not from_pos or not to_pos: # TODO handle better?
        flash('Invalid from/to position', 'danger')
        return redirect(g.redir)

    line = connection.line
    stops = []
    dt = connection.start_time
    delta = timedelta(0)
    for ls in LineStop.query.filter_by(line=line).order_by(LineStop.position):
        stop = {}
        stop['name'] = ls.stop.name
        stop['position'] = ls.position
        dt += timedelta(minutes=ls.time_delta)
        stop['time'] = dt
        stops.append(stop)
    operator = line.operator
    free_seats = connection.get_free_seats(from_pos, to_pos)



    return render_template('connection_detail.html', connection=connection, operator=operator, stops=stops, from_pos=from_pos, to_pos=to_pos, free_seats=free_seats)

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
        del g.operator
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
