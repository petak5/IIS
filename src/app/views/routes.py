from app import app
from app.models import db
from app.models.person_model import PersonModel


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
