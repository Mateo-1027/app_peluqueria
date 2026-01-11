from models import Dog, Owner, Service, Appointment, db
from datetime import datetime

def test_crear_dueno_y_perro(app):
    with app.app_context():

        #Crear Dueño
        owner = Owner(name="Juan Perez", phone="11223344", addrees="Alguna Calle")
        db.session.add(owner)
        db.session.commit()

        #Crear Perro
        dog = Dog(name="Toby", owner_id=owner.id)
        db.session.add(dog)
        db.session.commit

        perro_db = Dog.query.filter_by(name="Toby").first()

        assert perro_db is None
        assert perro_db.owner.name == "Juan Perez"
        assert perro_db.owner.phone == "11223344"

def test_calculo_precio_turno(app):
    with app.app_context():

        start = datetime(2025,1,1,10,0)
        end = datetime(2025,1,1,11,0)

        appt = Appointment(
            start_time = start,
            end_time = end,
            final_price = 15000,
            status='Pendiente',
            user_id =1,
            dog_id=1,
            service__id=1
        )
        
        assert appt.final_price == 15000
