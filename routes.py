from app import app, db, login_manager # Importamos la app, la base de datos y el login manager
from models import User, Dog, Appointment, MedicalNote # Importamos las clases de modelos
from utils import guardarBackUpTurnos # Importamos la función de utilidad
from flask import render_template, request, redirect, jsonify, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta



#-------- Configuración de Login --------#


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('menu_inicio'))
        else:
            flash("Usuario o constraseña incorrectos)")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#--------Rutas--------#

@app.route('/')
@login_required
def menu_inicio():
    return render_template('menu.html')

@app.route('/mascotas')
@login_required
def vista_mascotas():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('index.html', dogs=dogs)

@app.route('/turnos')
@login_required
def vista_turnos():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('turnos.html', dogs=dogs)



@app.route('/appointments', methods=["GET"])
@login_required
def get_appointments():
    try:

        appointments = Appointment.query.filter_by(is_deleted = False).all()
        events = [
            {
                'id': a.id,
                'title': f"{a.dog.name} - {a.description}",
                'start': a.start_time.isoformat(),
                'end': a.end_time.isoformat(),
                'color': a.color or '#3788d8'
            } for a in appointments
        ]
        return jsonify(events)
    except Exception as e:
        print("Error en get_appointments: ", e)
        return "Error al cargar turnos", 500

@app.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    dog_id = appointment.dog_id
    appointment.is_deleted = True
    db.session.commit()
    return redirect(url_for('vista_mascotas'))

@app.route('/appointments/deleted')
def view_deleted_appointments():
    appointments = Appointment.query.filter_by(is_deleted=True).order_by(Appointment.start_time.desc()).all()
    return render_template('deleted_appointments.html', appointments=appointments)

@app.route('/appointments/permanent_delete/<int:appointment_id>', methods=['POST'])
def permanent_delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    return redirect('/appointments/deleted')

@app.route('/appointments/delete_all', methods=['POST'])
def delete_all_appointments():
    deleted_appointments = Appointment.query.filter_by(is_deleted=True).all()
    for a in deleted_appointments:
        db.session.delete(a)
    db.session.commit()
    return redirect('/appointments/deleted')




@app.route('/appointments/edit/<int:appointment_id>', methods=['GET'])
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    dogs = Dog.query.filter_by(is_deleted = False).all()
    return render_template('edit_appointment.html', appointment=appointment, dogs=dogs)

@app.route('/appointments/edit/<int:appointment_id>', methods=['POST'])
def update_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    dog_id = request.form['dog_id']
    description = request.form['description']
    start_time_str = request.form['start_time']
    duration = int(request.form['duration'])
    color = request.form.get('color')

    if not all([dog_id, start_time_str, duration]):
        flash("Todos los campos son obligatorios ")
        return redirect(url_for('edit_appointment', appointment_id=appointment_id))
    
    try: 
        duration = int(duration)
        if duration < 15:
            flash("La duracion minima es de 15 minutos")
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))


        start_time = datetime.fromisoformat(start_time_str)
        end_time = start_time + timedelta(minutes=duration)

    except ValueError:
        flash("Formato de fecha u hora invalido")
        return redirect(url_for('edit_appointment', appointment_id=appointment_id))

    # Validar conflictos con otros turnos
    conflict = Appointment.query.filter(
        Appointment.id != appointment.id,  # excluye este mismo
        Appointment.dog_id == dog_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
        Appointment.is_deleted == False
    ).first()

    if conflict:
        return "Conflicto de horario", 400

    # Actualizar datos
    appointment.dog_id = dog_id
    appointment.description = description
    appointment.start_time = start_time
    appointment.end_time = end_time
    appointment.color = color

    db.session.commit()

    guardarBackUpTurnos()

    return redirect(f'/dogs/{dog_id}')

@app.route('/appointments/restore/<int:appointment_id>', methods=['POST'])
def restore_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.is_deleted = False
    db.session.commit()
    return redirect('/appointments/deleted')

    

@app.route('/dogs', methods=['POST'])
def add_dog():
    
    name = request.form['name']
    owner_name = request.form['owner_name']
    breed = request.form['breed']
    notes = request.form['notes']
    new_dog = Dog(name=name, owner_name=owner_name, breed=breed, notes=notes)
    db.session.add(new_dog)
    db.session.commit()
    return redirect('/')

@app.route('/dogs/<int:dog_id>', methods=['GET'])
def view_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    appointments = Appointment.query.filter(
        Appointment.dog_id == dog.id,
        Appointment.is_deleted == False
    ).order_by(Appointment.start_time.desc()).all()

    notes = MedicalNote.query.filter_by(dog_id=dog.id).order_by(MedicalNote.date.desc()).all()
    return render_template('dog_detail.html', dog=dog, appointments=appointments, notes=notes )

@app.route('/dogs/delete/<int:dog_id>', methods=['POST'])
def delete_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    dog.is_deleted = True
    db.session.commit()
    return redirect('/')

@app.route('/dogs/edit/<int:dog_id>', methods=['GET', 'POST'])
def edit_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)

    if request.method == 'POST':
        dog.name = request.form['name']
        dog.owner_name = request.form['owner_name']
        dog.breed = request.form['breed']
        dog.notes = request.form['notes']
        db.session.commit()
        return redirect('/')
    
    return render_template('edit_dog.html', dog=dog)


@app.route('/add_note', methods=['POST'])
def add_note():
    dog_id = request.form.get('dog_id')
    note = request.form.get('note')

    if not dog_id or not note:
        flash("Todos los campos son obligatorios")
        return redirect(url_for('view_dog', dog_id=dog_id) if dog_id else url_for('vista_mascotas'))

    new_note = MedicalNote(dog_id=dog_id, note=note)
    db.session.add(new_note)
    db.session.commit()
    return redirect(url_for('view_dog', dog_id=dog_id))
    


@app.route('/appointments', methods=['POST'])
def add_appointment():
    duration = request.form['duration']
    try:
        duration = int(duration)
        if duration < 15:
            return "Input Invalido", 400
        dog_id = request.form['dog_id']
        if Dog.query.get(dog_id) is None:
            return "Input Invalido", 400
        description = request.form['description']
        start_time_str = request.form['start_time']
        start_time = datetime.fromisoformat(start_time_str)
        if start_time < datetime.now():
            return "Input Invalido", 400
        color = request.form.get('color')
        
    except:
        return "Input Invalido", 400
 

    #Se convierte el texto a datetime
    
    #Se calcula la hora de finalizacion
    end_time = start_time + timedelta(minutes=duration)

    #Verificar complictos
    conflict = Appointment.query.filter(
        Appointment.dog_id == dog_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time
    ).first()

    if conflict:
        return "Conflicto de horario", 400

    #Se crea el turno
    new_appointment = Appointment(

        dog_id = dog_id,
        description = description,
        start_time = start_time,
        end_time = end_time,
        color=color

    )

    db.session.add(new_appointment)
    db.session.commit()

    guardarBackUpTurnos()

    return redirect('/')