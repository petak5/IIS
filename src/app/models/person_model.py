from . import db, base


class PersonModel(base.Base):
    __tablename__ = "persons_table"

    name = db.Column(db.String(80))
    age = db.Column(db.Integer)

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"{self.name}:{self.age}"
