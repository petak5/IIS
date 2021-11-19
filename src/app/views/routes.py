from app import app
from app.models import db
from app.models import PersonModel
from app.models import User
from flask import request, session
from sqlalchemy.exc import IntegrityError

# returns User if logged in, None otherwise
def get_session_user():
    user_id = session.get('user_id')
    user = None
    if user_id:
        user = User.query.get(user+id)
    return user

def login_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user is None:
        return None
    if user.auth(password):
        session['user_id'] = user.id
        return user
    else:
        return None

@app.route('/users')
def users():
    users = User.query.all()
    response = "Login Password<br>"
    for user in users:
        response += f"{user.login} {user.password}<br>"
    return response

@app.route('/user')
def user():
    user = get_session_user()
    if user:
        user = User.query.get(session['user_id'])
        return f"Currently logged in as {user.login}"
    else:
        return f"Currently logged out"

@app.route('/logout')
def logout():
    if session.get('user_id'):
        del session['user_id']
        return "Logged out"
    else:
        return "Not logged in"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return """
            <form action="login" method="post">
                <input type="text" placeholder="Login" name="login" required>
                <input type="password" placeholder="Password" name="password" required>
                <button type="submit">Login</button>
            </form>
        """
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            return "Both login and password are required parameters"

        user = login_user(login, password)
        if user is None:
            return "Invalid user or password"
        else:
            return f"Successfully logged in as {user.login}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return """
            <form action="register" method="post">
                <input type="text" placeholder="Login" name="login" required>
                <input type="password" placeholder="Password" name="password" required>
                <button type="submit">Register</button>
            </form>
        """
    if request.method == 'POST':
        login = request.form.get("login")
        password = request.form.get("password")
        if login is None or password is None:
            return "Both login and password are required parameters"
        user = User(login, password)
        db.session.add(user)
        try:
            db.session.commit()
            return f"Successfully registered {user.login}"
        except IntegrityError:
            return f"User '{user}' already exists"

@app.route('/')
@app.route('/hello')
def hello():
    return {"Hello": "World"}


@app.route('/add_person')
def add_person():
    new_person = PersonModel(name="John Doe", age=31)
    db.session.add(new_person)
    db.session.commit()
    return {"message": f"New person added: {new_person}"}


@app.route('/del_person')
def del_person():
    person = PersonModel.query.all()[-1]
    db.session.delete(person)
    db.session.commit()
    return {"message": f"Successfully deleted last person: {person}"}


@app.route('/persons')
def persons():
    all_persons = PersonModel.query.all()
    results = [
        {
            "id": person.id,
            "name": person.name,
            "age": person.age
        } for person in all_persons
    ]
    return {"count": len(results), "persons": results}
