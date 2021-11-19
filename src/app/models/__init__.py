from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

class User(Base):
    login = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False) # cleartext for now

    # gives admin privileges
    admin = db.Column(db.Boolean, nullable=False, default=False)

    # gives transport operator privileges
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), default=None)
    operator = db.relationship("Operator", foreign_keys=[operator_id])

    # gives crew privileges
    employer_id = db.Column(db.Integer, db.ForeignKey('operator.id'), default=None)
    employer = db.relationship("Operator", backref="employees", foreign_keys=[employer_id])

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def auth(self, password):
        return password == password # TODO hash

    def is_admin(self):
        return admin

    def is_operator(self):
        return operator_id is not None

    def is_crew(self):
        return employer_id is not None

class ConnectionStop(Base):
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'), primary_key=True)
    stop_id = db.Column(db.Integer, db.ForeignKey('stop.id'), primary_key=True)
    stop = db.relationship("Stop", back_populates="connections")
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'), primary_key=True)
    connection = db.relationship("Connection", back_populates="stops")
    date_time = db.Column(db.DateTime)

class Stop(Base):
    name = db.Column(db.String(128), nullable=False)
    connections = db.relationship(ConnectionStop, back_populates="stop")

    def __init__(self, name):
        self.name = name

# operator creates a proposal to create/modify a Stop
# which is then approved by an admin
class StopProposal(Base):
    # if the proposal is for a new stop this remains unset
    original = db.Column(db.Integer, db.ForeignKey('stop.id'), default=None)
    name = db.Column(db.String(128), nullable=False)

    def __init__(self, name, original=None):
        self.original = original
        self.name = name

class Connection(Base):
    name = db.Column(db.String(128), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    operator = db.relationship("Operator", backref="connections")
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    vehicle = db.relationship("Vehicle", backref="connections")
    stops = db.relationship(ConnectionStop, back_populates="connection")

    def __init__(self, name):
        self.name = name


class Vehicle(Base):
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    operator = db.relationship("Operator", backref="vehicles")
    num_seats = db.Column(db.Integer, nullable=False)
    last_known_stop = db.Column(db.Integer, db.ForeignKey('stop.id'), default=None)
    last_known_time = db.Column(db.DateTime, default=None)

    def __init__(self, operator):
        self.operator = operator

class Operator(Base):
    name = db.Column(db.String(128), nullable=False)

    def __init__(self, name):
        self.name = name

class Ticket(Base):
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    num_seats = db.Column(db.Integer, nullable=False, default=1)
    owner = db.relationship(User, backref="tikets")

    def __init__(self, owner):
        self.owner = owner
