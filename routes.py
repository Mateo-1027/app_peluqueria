# routes.py

from flask import Blueprint, render_template, request, redirect, jsonify, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager # Importa las extensiones
from models import User, Dog, Appointment, MedicalNote # Importa las clases de modelos
from utils import guardarBackUpTurnos # Importa la función de utilidad
from datetime import datetime, timedelta

# Crear un Blueprint
main = Blueprint('main', __name__)

#-------- Configuración de Login --------#

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.menu_inicio'))
        else:
            flash("Usuario o contraseña incorrectos")
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

#-------- Rutas Principales --------#

@main.route('/')
@login_required
def menu_inicio():
    return render_template('menu.html')

@main.route('/mascotas')
@login_required
def vista_mascotas():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('index.html', dogs=dogs)

@main.route('/turnos')
@login_required
def vista_turnos():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('turnos.html', dogs=dogs)

#-------- Rutas de Citas --------#

@main.route('/appointments', methods=["GET"])
@login_required
def get_appointments():
    try:
        appointments = Appointment.query.filter_by(is_deleted=False).all()
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
        return jsonify({'error': 'Error al cargar turnos'}), 500

@main.route('/appointments', methods=['POST'])
@login_required
def add_appointment():
    try:
        duration = int(request.form.get('duration'))
        dog_id = request.form.get('dog_id')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        color = request.form.get('color')

        if duration < 15:
            flash("La duración mínima es de 15 minutos.")
            return redirect(url_for('main.vista_turnos'))

        dog = Dog.query.get(dog_id)
        if dog is None or dog.is_deleted:
            flash("Mascota inválida.")
            return redirect(url_for('main.vista_turnos'))

        start_time = datetime.fromisoformat(start_time_str)
        if start_time < datetime.now():
            flash("No puedes crear un turno en el pasado.")
            return redirect(url_for('main.vista_turnos'))
    except (ValueError, TypeError):
        flash("Datos de entrada inválidos.")
        return redirect(url_for('main.vista_turnos'))
        
    end_time = start_time + timedelta(minutes=duration)

    conflict = Appointment.query.filter(
        Appointment.dog_id == dog_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
        Appointment.is_deleted == False
    ).first()

    if conflict:
        flash("Conflicto de horario: Ya existe un turno en ese horario para esta mascota.")
        return redirect(url_for('main.vista_turnos'))

    new_appointment = Appointment(
        dog_id=dog_id,
        description=description,
        start_time=start_time,
        end_time=end_time,
        color=color
    )

    db.session.add(new_appointment)
    db.session.commit()
    guardarBackUpTurnos()
    
    return redirect(url_for('main.vista_turnos'))


@main.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.is_deleted = True
    db.session.commit()
    return redirect(url_for('main.vista_turnos'))

@main.route('/appointments/deleted')
@login_required
def view_deleted_appointments():
    appointments = Appointment.query.filter_by(is_deleted=True).order_by(Appointment.start_time.desc()).all()
    return render_template('deleted_appointments.html', appointments=appointments)

@main.route('/appointments/permanent_delete/<int:appointment_id>', methods=['POST'])
@login_required
def permanent_delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    return redirect(url_for('main.view_deleted_appointments'))

@main.route('/appointments/delete_all', methods=['POST'])
@login_required
def delete_all_appointments():
    deleted_appointments = Appointment.query.filter_by(is_deleted=True).all()
    for a in deleted_appointments:
        db.session.delete(a)
    db.session.commit()
    return redirect(url_for('main.view_deleted_appointments'))

@main.route('/appointments/edit/<int:appointment_id>', methods=['GET'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('edit_appointment.html', appointment=appointment, dogs=dogs)

@main.route('/appointments/edit/<int:appointment_id>', methods=['POST'])
@login_required
def update_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    dog_id = request.form.get('dog_id')
    description = request.form.get('description')
    start_time_str = request.form.get('start_time')
    duration = request.form.get('duration')
    color = request.form.get('color')

    if not all([dog_id, start_time_str, duration]):
        flash("Todos los campos son obligatorios.")
        return redirect(url_for('main.edit_appointment', appointment_id=appointment_id))
    
    try: 
        duration = int(duration)
        if duration < 15:
            flash("La duración mínima es de 15 minutos.")
            return redirect(url_for('main.edit_appointment', appointment_id=appointment_id))

        start_time = datetime.fromisoformat(start_time_str)
        end_time = start_time + timedelta(minutes=duration)

    except ValueError:
        flash("Formato de fecha u hora inválido.")
        return redirect(url_for('main.edit_appointment', appointment_id=appointment_id))

    conflict = Appointment.query.filter(
        Appointment.id != appointment.id,
        Appointment.dog_id == dog_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
        Appointment.is_deleted == False
    ).first()

    if conflict:
        flash("Conflicto de horario: Ya existe un turno en ese horario para esta mascota.")
        return redirect(url_for('main.edit_appointment', appointment_id=appointment_id))

    appointment.dog_id = dog_id
    appointment.description = description
    appointment.start_time = start_time
    appointment.end_time = end_time
    appointment.color = color

    db.session.commit()
    guardarBackUpTurnos()

    return redirect(url_for('main.view_dog', dog_id=dog_id))

@main.route('/appointments/restore/<int:appointment_id>', methods=['POST'])
@login_required
def restore_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.is_deleted = False
    db.session.commit()
    return redirect(url_for('main.view_deleted_appointments'))


#-------- Rutas de Mascotas --------#

@main.route('/dogs', methods=['POST'])
@login_required
def add_dog():
    name = request.form.get('name')
    owner_name = request.form.get('owner_name')
    notes = request.form.get('notes')

    if not name:
        flash("El nombre de la mascota es obligatorio.")
        return redirect(url_for('main.vista_mascotas'))
    
    new_dog = Dog(name=name, owner_name=owner_name, notes=notes)
    db.session.add(new_dog)
    db.session.commit()
    return redirect(url_for('main.vista_mascotas'))

@main.route('/dogs/<int:dog_id>', methods=['GET'])
@login_required
def view_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    appointments = Appointment.query.filter(
        Appointment.dog_id == dog.id,
        Appointment.is_deleted == False
    ).order_by(Appointment.start_time.desc()).all()

    notes = MedicalNote.query.filter_by(dog_id=dog.id).order_by(MedicalNote.date.desc()).all()
    return render_template('dog_detail.html', dog=dog, appointments=appointments, notes=notes)

@main.route('/dogs/delete/<int:dog_id>', methods=['POST'])
@login_required
def delete_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    dog.is_deleted = True
    db.session.commit()
    return redirect(url_for('main.vista_mascotas'))

@main.route('/dogs/edit/<int:dog_id>', methods=['GET', 'POST'])
@login_required
def edit_dog(dog_id):
    dog = Dog.query.get_or_404(dog_id)

    if request.method == 'POST':
        dog.name = request.form.get('name')
        dog.owner_name = request.form.get('owner_name')
        dog.notes = request.form.get('notes')

        if not dog.name:
            flash("El nombre de la mascota es obligatorio.")
            return render_template('edit_dog.html', dog=dog)

        db.session.commit()
        return redirect(url_for('main.vista_mascotas'))
    
    return render_template('edit_dog.html', dog=dog)

@main.route('/add_note', methods=['POST'])
@login_required
def add_note():
    dog_id = request.form.get('dog_id')
    note = request.form.get('note')
    
    if not dog_id or not note:
        flash("Error: Se requiere el ID de la mascota y la nota.")
        return redirect(url_for('main.view_dog', dog_id=dog_id) if dog_id else url_for('main.vista_mascotas'))
        
    new_note = MedicalNote(dog_id=dog_id, note=note)
    db.session.add(new_note)
    db.session.commit()
    return redirect(url_for('main.view_dog', dog_id=dog_id))