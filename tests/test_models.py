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
        
        # 3. Crear ServiceCategory y ServiceSize y Service
        from models import Service, ServiceCategory, ServiceSize
        
        category = ServiceCategory(name="Baño", description="Solo baño", display_order=1)
        db.session.add(category)
        db.session.commit()
        
        size = ServiceSize(name="Chico", display_order=1)
        db.session.add(size)
        db.session.commit()
        
        service = Service(
            category_id=category.id,
            size_id=size.id,
            base_price=10000,
            duration_minutes=60
        )
        db.session.add(service)
        db.session.commit()
        
        # 4. Crear Professional (peluquera)
        from models import Professional
        prof = Professional(name="Ana Martinez", commission_percentage=50.0)
        db.session.add(prof)
        db.session.commit()
        
        # 5. Crear Appointment
        start = datetime(2025, 1, 1, 10, 0)
        end = datetime(2025, 1, 1, 11, 0)
        
        appt = Appointment(
            start_time=start,
            end_time=end,
            final_price=15000,
            status='Pendiente',
            professional_id=prof.id,
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
