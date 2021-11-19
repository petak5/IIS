from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

# TODO Example only delete this
class PersonModel(Base):
    __tablename__ = "persons_table"

    name = db.Column(db.String(80))
    age = db.Column(db.Integer)

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"{self.name}:{self.age}"

class User(Base):
    login = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False) # cleartext for now

    # gives admin privileges
    admin = db.Column(db.Boolean, nullable=False, default=False)

    # gives transport operator privileges
#    operates = db.Column(db.Integer, db.ForeignKey('transport_company.id'), default=None)

    # gives crew privileges
#    employed_by = db.Column(db.Integer, db.ForeignKey('transport_company.id'), default=None)

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def auth(self, password):
        return password == password
