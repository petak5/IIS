from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

class User(Base):
    login = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(256)) # cleartext for now, null disables login

    # gives admin privileges
    admin = db.Column(db.Boolean, nullable=False, default=False)

    # operator privileges given if not null
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), default=None)
    operator = db.relationship("Operator", backref=db.backref("manager", uselist=False), foreign_keys=[operator_id])

    # gives crew privileges
    employer_id = db.Column(db.Integer, db.ForeignKey('operator.id'), default=None)
    employer = db.relationship("Operator", backref="employees", foreign_keys=[employer_id])

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def auth(self, password):
        return self.password == password # TODO hash

    def is_admin(self):
        return self.admin

    def is_operator(self):
        return self.operator_id is not None

    def is_crew(self):
        return self.employer_id is not None

# operator creates a proposal to create/modify a Stop
# which is then approved by an admin
class StopProposal(Base):
    # if the proposal is for a new stop this remains unset
    original_id = db.Column(db.Integer, db.ForeignKey('stop.id'), default=None)
    original = db.relationship("Stop", backref=db.backref("proposals", cascade='all,delete-orphan'))
    name = db.Column(db.String(128), nullable=False)

    def __init__(self, name, original=None):
        self.original = original
        self.name = name

class Stop(Base):
    name = db.Column(db.String(128), nullable=False)
    lines = db.relationship("LineStop", back_populates="stop")

    def __init__(self, name):
        self.name = name

class Line(Base):
    name = db.Column(db.String(128), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    operator = db.relationship("Operator", backref=db.backref("lines", cascade='all, delete-orphan'))
    stops = db.relationship("LineStop", back_populates="line", cascade='all,delete-orphan')

    def __init__(self, name, operator):
        self.name = name
        self.operator = operator

class LineStop(Base):
    stop_id = db.Column(db.Integer, db.ForeignKey('stop.id'))
    stop = db.relationship("Stop", back_populates="lines")
    line_id = db.Column(db.Integer, db.ForeignKey('line.id'), nullable=False)
    line = db.relationship("Line", back_populates="stops")
    position = db.Column(db.Integer, nullable=False)
    time_delta = db.Column(db.Integer, default=0)

    # TODO: Test if this actually works
    db.UniqueConstraint('position')

    def __init__(self, position):
        self.position = position

class Connection(Base):
    start_time = db.Column(db.DateTime, nullable=False)
    line_id = db.Column(db.Integer, db.ForeignKey('line.id'), nullable=False)
    line = db.relationship("Line", backref=db.backref("connections", cascade='all, delete-orphan'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    vehicle = db.relationship("Vehicle", backref=db.backref("connections", cascade='all, delete-orphan'))

    def get_free_seats(self, from_pos, to_pos):
        if not LineStop.query.filter_by(line=self.line, position=from_pos).first():
            return 0
        if not LineStop.query.filter_by(line=self.line, position=to_pos).first():
            return 0
        occupied_seats = sum(ticket.num_seats for ticket in Ticket.query.filter_by(connection=self).filter(Ticket.from_pos <= from_pos).filter(Ticket.to_pos >= from_pos))
        return self.vehicle.num_seats - occupied_seats

    def __init__(self, start_time):
        self.start_time = start_time

class Vehicle(Base):
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    operator = db.relationship("Operator", backref=db.backref("vehicles", cascade='all, delete-orphan'))
    description = db.Column(db.String(128), nullable=False, default='')
    num_seats = db.Column(db.Integer, nullable=False)
    last_known_stop_id = db.Column(db.Integer, db.ForeignKey('stop.id'), default=None)
    last_known_stop = db.relationship("Stop")
    last_known_time = db.Column(db.DateTime, default=None)

    def __init__(self, operator):
        self.operator = operator

class Operator(Base):
    name = db.Column(db.String(128), nullable=False)
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
#    user = db.relationship(User, backref="operator", foreign_keys=[user_id], uselist=False)

    def __init__(self, name):
        self.name = name

class Ticket(Base):
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship(User, backref=db.backref("tickets", cascade='all, delete-orphan'))
    num_seats = db.Column(db.Integer, nullable=False, default=1)
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'))
    connection = db.relationship(Connection, backref=db.backref("tickets", cascade='all, delete-orphan')) # TODO
    from_pos = db.Column(db.Integer, nullable=False)
    to_pos = db.Column(db.Integer, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, owner):
        self.owner = owner
