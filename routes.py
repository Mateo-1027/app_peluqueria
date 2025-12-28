# routes.py

from flask import Blueprint, render_template, request, redirect, jsonify, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager # Importa las extensiones
from models import User, Dog, Appointment, MedicalNote # Importa las clases de modelos
from utils import guardarBackUpTurnos # Importa la función de utilidad
from datetime import datetime, timedelta
from forms import LoginForm, DogForm, AppointmentForm

# Crear un Blueprint
main = Blueprint('main', __name__)

#-------- Configuración de Login --------#

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.menu_inicio'))
        else:
            flash("Usuario o contraseña incorrectos")
    return render_template('login.html', form=form)

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
    form = DogForm() # <--- Lo nuevo: Creamos el form vacío
    return render_template('index.html', dogs=dogs, form=form)

@main.route('/turnos')
@login_required
def vista_turnos():
    
    dogs = Dog.query.filter_by(is_deleted=False).all()
    form = AppointmentForm()
    form.dog_id.choices = [(d.id, f"{d.name} ({d.owner_name or 'Sin dueño'})") for d in dogs]

    return render_template('turnos.html', dogs=dogs, form=form)

@main.route('/api/dogs')
@login_required
def get_dogs_json():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    dogs_list = [
        {
            'id': dog.id,
            'name': dog.name,
            'owner_name': dog.owner_name,
        }
        for dog in dogs
    ]
    return jsonify(dogs_list)

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
    form = AppointmentForm()
   
    dogs = Dog.query.filter_by(is_deleted=False).all()
    form.dog_id.choices = [(d.id, d.name) for d in dogs]

    if form.validate_on_submit():

        # Cálculo de fecha fin
        end_time = form.start_time.data + timedelta(minutes=form.duration.data)

        new_appointment = Appointment(
            dog_id=form.dog_id.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=end_time,
            color=form.color.data
        )

        db.session.add(new_appointment)
        db.session.commit()
        guardarBackUpTurnos()
        flash("Turno creado exitosamente.")
        return redirect(url_for('main.vista_turnos'))

    else:
        # Si falla, volvemos a mostrar la página con los errores
        return render_template('turnos.html', dogs=dogs, form=form)

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

@main.route('/appointments/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    form = AppointmentForm(obj=appointment) # Carga los datos del turno en el formulario

    # Cargar lista de perros
    dogs = Dog.query.filter_by(is_deleted=False).all()
    form.dog_id.choices = [(d.id, f"{d.name} ({d.owner_name})") for d in dogs]

    if form.validate_on_submit():
        # Actualizar datos
        appointment.dog_id = form.dog_id.data
        appointment.description = form.description.data
        appointment.start_time = form.start_time.data
        appointment.color = form.color.data

        # Recalcular hora fin basado en la nueva duración
        appointment.end_time = form.start_time.data + timedelta(minutes=form.duration.data)

        db.session.commit()
        guardarBackUpTurnos()
        flash("Turno actualizado.")
        return redirect(url_for('main.vista_turnos'))

    # Un truco para pre-llenar la duración que no es un campo directo de la BD
    if request.method == 'GET':
        duration_minutes = (appointment.end_time - appointment.start_time).seconds // 60
        form.duration.data = duration_minutes

    return render_template('edit_appointment.html', form=form, appointment=appointment)

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
    form = DogForm()
    

    if form.validate_on_submit():
        new_dog = Dog(
            name=form.name.data,       
            owner_name=form.owner_name.data,
            notes=form.notes.data
        )
        db.session.add(new_dog)
        db.session.commit()
        flash('Mascota agregada correctamente.')
        return redirect(url_for('main.vista_mascotas'))
 
    dogs = Dog.query.filter_by(is_deleted=False).all()
    return render_template('index.html', dogs=dogs, form=form)

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
    
    # Este truco carga los datos del perro en el formulario automáticamente
    form = DogForm(obj=dog) 
    
    if form.validate_on_submit():
        # Este otro truco pasa los datos del formulario al perro
        form.populate_obj(dog) 
        
        db.session.commit()
        flash('Mascota actualizada.')
        return redirect(url_for('main.vista_mascotas'))
    
    return render_template('edit_dog.html', form=form, dog=dog)


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