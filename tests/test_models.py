from models import Dog, Owner, Service, Appointment, db
from datetime import datetime

def test_crear_dueno_y_perro(app):
    with app.app_context():

        #Crear Dueño
        owner = Owner(name="Juan Perez", phone="11223344", addres="Alguna Calle")
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
    """Prueba simple de guardado de precio en Turno"""
    with app.app_context():
        # Setup básico
        start = datetime(2025, 1, 1, 10, 0)
        end = datetime(2025, 1, 1, 11, 0)
        
        # Guardamos un turno con precio final manual (ya que la lógica está en la ruta)
        appt = Appointment(
            start_time=start,
            end_time=end,
            final_price=15000,
            status='Pendiente',
            user_id=1, # Asumiendo que el fixture crea un usuario ID 1
            dog_id=1,   # Necesitaríamos crear un perro antes, pero para unit test del campo sirve
            service_id=1
        )
        
        # Nota: En un test real deberías crear Service, Dog y User antes.
        # Aquí solo probamos que el modelo
