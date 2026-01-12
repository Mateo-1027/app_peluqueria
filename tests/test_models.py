from models import Dog, Owner, Service, Appointment, db
from datetime import datetime

def test_crear_dueno_y_perro(app):
    with app.app_context():

        # Crear Dueño
        owner = Owner(name="Juan Perez", phone="11223344", address="Alguna Calle")
        db.session.add(owner)
        db.session.commit()

        # Crear Perro
        dog = Dog(name="Toby", owner_id=owner.id)
        db.session.add(dog)
        db.session.commit()

        perro_db = Dog.query.filter_by(name="Toby").first()

        assert perro_db is not None
        assert perro_db.owner.name == "Juan Perez"
        assert perro_db.owner.phone == "11223344"

def test_calculo_precio_turno(app):
    """Prueba de guardado de precio en Appointment"""
    with app.app_context():
        # 1. Crear Owner
        owner = Owner(name="Maria Lopez", phone="55667788", address="Calle Falsa 123")
        db.session.add(owner)
        db.session.commit()
        
        # 2. Crear Dog
        dog = Dog(name="Rex", owner_id=owner.id)
        db.session.add(dog)
        db.session.commit()
        
        # 3. Obtener Service (ya creado por create_app en conftest)
        from models import Service
        service = Service.query.first()
        
        # 4. Obtener User (creado en conftest)
        from models import User
        user = User.query.filter_by(username="admin").first()
        
        # 5. Crear Appointment
        start = datetime(2025, 1, 1, 10, 0)
        end = datetime(2025, 1, 1, 11, 0)
        
        appt = Appointment(
            start_time=start,
            end_time=end,
            final_price=15000,
            status='Pendiente',
            user_id=user.id,
            dog_id=dog.id,
            service_id=service.id
        )
        db.session.add(appt)
        db.session.commit()
        
        # 6. Verificar
        appt_db = Appointment.query.first()
        assert appt_db is not None
        assert appt_db.final_price == 15000
        assert appt_db.dog.name == "Rex"
