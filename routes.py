# routes.py

from flask import Blueprint, render_template, request, redirect, jsonify, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager 
from models import User, Dog, Appointment, MedicalNote, Service, ServiceCategory, ServiceSize, Item, Owner, Professional, Payment
from utils import guardarBackUpTurnos 
from datetime import datetime, timedelta
from forms import LoginForm, DogForm, AppointmentForm, ServiceForm, ServiceCategoryForm, ServiceSizeForm, ItemForm, CheckoutForm 
from sqlalchemy import or_, func

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
def index():
    if current_user.is_authenticated:
        return render_template('menu.html')
    else:
        return redirect(url_for('main.login'))

@main.route('/menu')
@login_required
def menu_inicio():
    return render_template('menu.html')

@main.route('/mascotas')
@login_required
def vista_mascotas():
    dogs = []
    form = DogForm() 
    return render_template('index.html', dogs=dogs, form=form)

@main.route('/turnos')
@login_required
def vista_turnos():

    services = Service.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    professionals = Professional.query.filter_by(is_active=True).all()
    
    # Agrupar servicios por categoría
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order).all()
    services_by_category = {}
    for category in categories:
        category_services = [s for s in services if s.category_id == category.id]
        if category_services:
            services_by_category[category] = category_services
    
    form = AppointmentForm()
  
    form.service_id.choices = [(s.id, f"{s.name} - ${s.base_price:,.0f}") for s in services]
    form.item_ids.choices = [(i.id, f"{i.name} (+${i.price:,.0f})") for i in items]
    form.professional_id.choices = [(p.id, p.name) for p in professionals]

    return render_template('turnos.html', dogs=[], form=form, services_by_category=services_by_category)

@main.route('/api/dogs')
@login_required
def get_dogs_json():
    dogs = Dog.query.filter_by(is_deleted=False).all()
    dogs_list = [
        {
            'id': dog.id,
            'name': dog.name,
            'owner_name': dog.owner.name,
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
   
    # Cargar opciones para el formulario
    services = Service.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    professionals = Professional.query.filter_by(is_active=True).all()
    
    form.service_id.choices = [(s.id, s.name) for s in services]
    form.item_ids.choices = [(i.id, i.name) for i in items]
    form.professional_id.choices = [(p.id, p.name) for p in professionals]

    if form.validate_on_submit():
        # Obtener el servicio seleccionado
        service = Service.query.get(form.service_id.data)
        
        # Calcular fecha fin usando la duración MANUAL del usuario
        end_time = form.start_time.data + timedelta(minutes=form.duration.data)

        # Calcular precio total (servicio + items adicionales)
        final_price = service.base_price
        selected_items = Item.query.filter(Item.id.in_(form.item_ids.data)).all() if form.item_ids.data else []
        for item in selected_items:
            final_price += item.price

        # Crear el turno
        new_appointment = Appointment(
            dog_id=form.dog_id.data,
            service_id=form.service_id.data,
            professional_id=form.professional_id.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=end_time,
            total_amount=final_price,
            final_price=final_price,
            color=form.color.data,
            status='Pendiente'
        )

        db.session.add(new_appointment)
        db.session.flush()  # Para obtener el ID del appointment
        
        # Asociar items adicionales
        new_appointment.items = selected_items
        
        db.session.commit()
        guardarBackUpTurnos()
        flash(f"Turno creado exitosamente. Total: ${final_price:,.0f}")
        return redirect(url_for('main.vista_turnos'))

    else:

        categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order).all()
        services_by_category = {}
        for category in categories:
            category_services = [s for s in services if s.category_id == category.id]
            if category_services:
                services_by_category[category] = category_services

        
        return render_template('turnos.html', dogs=[], form=form, services_by_category=services_by_category)

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
    form = AppointmentForm(obj=appointment)

    # Cargar listas para opciones del formulario
    services = Service.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    professionals = Professional.query.filter_by(is_active=True).all()
    
    form.service_id.choices = [(s.id, f"{s.name} - ${s.base_price:,.0f}") for s in services]
    form.item_ids.choices = [(i.id, f"{i.name} (+${i.price:,.0f})") for i in items]
    form.professional_id.choices = [(p.id, p.name) for p in professionals]

    if form.validate_on_submit():
        # Obtener el servicio
        service = Service.query.get(form.service_id.data)
        
        # Actualizar datos básicos
        appointment.dog_id = form.dog_id.data
        appointment.service_id = form.service_id.data
        appointment.professional_id = form.professional_id.data
        appointment.description = form.description.data
        appointment.start_time = form.start_time.data
        appointment.color = form.color.data

        # Recalcular hora fin basado en la duración MANUAL
        appointment.end_time = form.start_time.data + timedelta(minutes=form.duration.data)
        
        # Recalcular precio total
        final_price = service.base_price
        selected_items = Item.query.filter(Item.id.in_(form.item_ids.data)).all() if form.item_ids.data else []
        for item in selected_items:
            final_price += item.price
        appointment.final_price = final_price
        
        # Actualizar items adicionales
        appointment.items = selected_items

        db.session.commit()
        guardarBackUpTurnos()
        flash(f"Turno actualizado. Total: ${final_price:,.0f}")
        return redirect(url_for('main.vista_turnos'))

    # Pre-llenar los items y duración al cargar el formulario
    if request.method == 'GET':
        form.dog_id.data = appointment.dog_id
        form.item_ids.data = [item.id for item in appointment.items]
        # Calcular duración actual en minutos
        duration_minutes = (appointment.end_time - appointment.start_time).seconds // 60
        form.duration.data = duration_minutes

    return render_template('edit_appointment.html', form=form, appointment=appointment, services=services)

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

        owner = None
        if form.owner_phone.data:
            owner = Owner.query.filter_by(phone=form.owner_phone.data).first()

        if not owner:
            owner = Owner(
                name = form.owner_name.data,
                phone=form.owner_phone.data,
                address=form.address.data
            )
            db.session.add(owner)
            db.session.flush()
        else:
            # Si el owner existe, actualizamos sus datos 
            owner.name = form.owner_name.data
            owner.phone = form.owner_phone.data
            owner.address = form.address.data

        new_dog = Dog(
            name=form.name.data,       
            owner_id=owner.id,
            notes=form.notes.data
        )
        db.session.add(new_dog)
        db.session.commit()
        flash('Mascota agregada correctamente.')
        return redirect(url_for('main.vista_mascotas'))
 
    dogs = []
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
    form = DogForm(obj=dog) 
    
    if request.method == 'GET':
        form.owner_name.data = dog.owner.name
        form.owner_phone.data = dog.owner.phone
        form.address.data = dog.owner.address

    if form.validate_on_submit():
        
        #Actualizar Datos de la mascota
        dog.name = form.name.data
        dog.notes = form.notes.data

        #Actualiza dato del dueño (Para todas sus mascotas)
        dog.owner.name = form.owner_name.data
        dog.owner.phone = form.owner_phone.data
        dog.owner.address = form.address.data

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

@main.route('/api/dogs/search')
@login_required
def search_dogs_api():

    query = request.args.get('q', '').strip()
    base_query = Dog.query.join(Owner).filter(Dog.is_deleted == False)

    if query:
        if query.isdigit():
            # Buscar por ID o por nombre (perro o dueño)
            base_query = base_query.filter(
                or_(
                    Dog.name.ilike(f'%{query}%'),
                    Dog.id == int(query),
                    Owner.name.ilike(f'%{query}%')
                )
            )
        else:
            # Buscar por nombre del perro o nombre del dueño
            base_query = base_query.filter(
                or_(
                    Dog.name.ilike(f'%{query}%'),
                    Owner.name.ilike(f'%{query}%')
                )
            )

    results = base_query.order_by(Dog.name.asc()).limit(50).all()

    dogs_data = [{
        'id': d.id,
        'name': d.name,
        'owner_name': d.owner.name
    } for d in results]

    return jsonify(dogs_data)


@main.route('/api/owners/search')
@login_required
def search_owners_api():
    """Buscar owners por nombre o teléfono para autocompletado"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    # Buscar por nombre o teléfono
    results = Owner.query.filter(
        or_(
            Owner.name.ilike(f'%{query}%'),
            Owner.phone.ilike(f'%{query}%')
        )
    ).order_by(Owner.name.asc()).limit(20).all()
    
    owners_data = [{
        'id': o.id,
        'name': o.name,
        'phone': o.phone or '',
        'address': o.address or ''
    } for o in results]
    
    return jsonify(owners_data)


#-------- Rutas de Gestión de Servicios --------#

@main.route('/services')
@login_required
def list_services():
    """Vista para listar todos los servicios"""
    services = Service.query.all()
    return render_template('services/list.html', services=services)

@main.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    """Agregar un nuevo servicio"""
    form = ServiceForm()
    
    # Cargar opciones para categorías y tamaños
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order).all()
    sizes = ServiceSize.query.filter_by(is_active=True).order_by(ServiceSize.display_order).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.size_id.choices = [(s.id, s.name) for s in sizes]
    
    if form.validate_on_submit():
        new_service = Service(
            category_id=form.category_id.data,
            size_id=form.size_id.data,
            description=form.description.data,
            base_price=form.base_price.data,
            duration_minutes=form.duration_minutes.data,
            is_active=bool(form.is_active.data)
        )
        db.session.add(new_service)
        db.session.commit()
        flash(f'Servicio "{new_service.name}" agregado exitosamente.')
        return redirect(url_for('main.list_services'))
    
    return render_template('services/form.html', form=form, title='Agregar Servicio')

@main.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    """Editar un servicio existente"""
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    
    # Cargar opciones para categorías y tamaños
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order).all()
    sizes = ServiceSize.query.filter_by(is_active=True).order_by(ServiceSize.display_order).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.size_id.choices = [(s.id, s.name) for s in sizes]
    
    if form.validate_on_submit():
        service.category_id = form.category_id.data
        service.size_id = form.size_id.data
        service.description = form.description.data
        service.base_price = form.base_price.data
        service.duration_minutes = form.duration_minutes.data
        service.is_active = bool(form.is_active.data)
        
        db.session.commit()
        flash(f'Servicio "{service.name}" actualizado.')
        return redirect(url_for('main.list_services'))
    
    # Pre-llenar el campo is_active
    if request.method == 'GET':
        form.is_active.data = 1 if service.is_active else 0
    
    return render_template('services/form.html', form=form, title='Editar Servicio', service=service)

@main.route('/services/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    """Desactivar un servicio"""
    service = Service.query.get_or_404(service_id)
    service.is_active = False
    db.session.commit()
    flash(f'Servicio "{service.name}" desactivado.')
    return redirect(url_for('main.list_services'))

@main.route('/services/permanent_delete/<int:service_id>', methods=['POST'])
@login_required
def permanent_delete_service(service_id):
    """Eliminar permanentemente un servicio"""
    service = Service.query.get_or_404(service_id)
    service_name = service.name
    db.session.delete(service)
    db.session.commit()
    flash(f'Servicio "{service_name}" eliminado permanentemente.')
    return redirect(url_for('main.list_services'))


#-------- Rutas de Gestión de Items Adicionales --------#

@main.route('/items')
@login_required
def list_items():
    """Vista para listar todos los items adicionales"""
    items = Item.query.all()
    return render_template('items/list.html', items=items)

@main.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Agregar un nuevo item adicional"""
    form = ItemForm()
    if form.validate_on_submit():
        new_item = Item(
            name=form.name.data,
            price=form.price.data,
            is_active=bool(form.is_active.data)
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f'Item "{new_item.name}" agregado exitosamente.')
        return redirect(url_for('main.list_items'))
    
    return render_template('items/form.html', form=form, title='Agregar Adicional')

@main.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """Editar un item adicional existente"""
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.price = form.price.data
        item.is_active = bool(form.is_active.data)
        
        db.session.commit()
        flash(f'Item "{item.name}" actualizado.')
        return redirect(url_for('main.list_items'))
    
    # Pre-llenar el campo is_active
    if request.method == 'GET':
        form.is_active.data = 1 if item.is_active else 0
    
    return render_template('items/form.html', form=form, title='Editar Adicional', item=item)

@main.route('/items/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    """Desactivar un item adicional"""
    item = Item.query.get_or_404(item_id)
    item.is_active = False
    db.session.commit()
    flash(f'Item "{item.name}" desactivado.')
    return redirect(url_for('main.list_items'))


#-------- Rutas de Gestión de Categorías de Servicio --------#

@main.route('/services/categories')
@login_required
def list_categories():
    """Vista para listar todas las categorías de servicio"""
    categories = ServiceCategory.query.order_by(ServiceCategory.display_order).all()
    return render_template('services/categories_list.html', categories=categories)

@main.route('/services/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Agregar una nueva categoría de servicio"""
    form = ServiceCategoryForm()
    if form.validate_on_submit():
        new_category = ServiceCategory(
            name=form.name.data,
            description=form.description.data,
            display_order=form.display_order.data or 0,
            is_active=bool(form.is_active.data)
        )
        db.session.add(new_category)
        db.session.commit()
        flash(f'Categoría "{new_category.name}" agregada exitosamente.')
        return redirect(url_for('main.list_categories'))
    
    return render_template('services/category_form.html', form=form, title='Agregar Categoría')

@main.route('/services/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Editar una categoría de servicio existente"""
    category = ServiceCategory.query.get_or_404(category_id)
    form = ServiceCategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.display_order = form.display_order.data or 0
        category.is_active = bool(form.is_active.data)
        
        db.session.commit()
        flash(f'Categoría "{category.name}" actualizada.')
        return redirect(url_for('main.list_categories'))
    
    # Pre-llenar campos
    if request.method == 'GET':
        form.is_active.data = 1 if category.is_active else 0
        form.display_order.data = category.display_order
    
    return render_template('services/category_form.html', form=form, title='Editar Categoría', category=category)

@main.route('/services/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Desactivar una categoría de servicio"""
    category = ServiceCategory.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    flash(f'Categoría "{category.name}" desactivada.')
    return redirect(url_for('main.list_categories'))


#-------- Rutas de Gestión de Tamaños de Servicio --------#

@main.route('/services/sizes')
@login_required
def list_sizes():
    """Vista para listar todos los tamaños de servicio"""
    sizes = ServiceSize.query.order_by(ServiceSize.display_order).all()
    return render_template('services/sizes_list.html', sizes=sizes)

@main.route('/services/sizes/add', methods=['GET', 'POST'])
@login_required
def add_size():
    """Agregar un nuevo tamaño de servicio"""
    form = ServiceSizeForm()
    if form.validate_on_submit():
        new_size = ServiceSize(
            name=form.name.data,
            display_order=form.display_order.data or 0,
            is_active=bool(form.is_active.data)
        )
        db.session.add(new_size)
        db.session.commit()
        flash(f'Tamaño "{new_size.name}" agregado exitosamente.')
        return redirect(url_for('main.list_sizes'))
    
    return render_template('services/size_form.html', form=form, title='Agregar Tamaño')

@main.route('/services/sizes/edit/<int:size_id>', methods=['GET', 'POST'])
@login_required
def edit_size(size_id):
    """Editar un tamaño de servicio existente"""
    size = ServiceSize.query.get_or_404(size_id)
    form = ServiceSizeForm(obj=size)
    
    if form.validate_on_submit():
        size.name = form.name.data
        size.display_order = form.display_order.data or 0
        size.is_active = bool(form.is_active.data)
        
        db.session.commit()
        flash(f'Tamaño "{size.name}" actualizado.')
        return redirect(url_for('main.list_sizes'))
    
    # Pre-llenar campos
    if request.method == 'GET':
        form.is_active.data = 1 if size.is_active else 0
        form.display_order.data = size.display_order
    
    return render_template('services/size_form.html', form=form, title='Editar Tamaño', size=size)

@main.route('/services/sizes/delete/<int:size_id>', methods=['POST'])
@login_required
def delete_size(size_id):
    """Desactivar un tamaño de servicio"""
    size = ServiceSize.query.get_or_404(size_id)
    size.is_active = False
    db.session.commit()
    flash(f'Tamaño "{size.name}" desactivado.')
    return redirect(url_for('main.list_sizes'))

@main.route('/appointments/<int:appointment_id>/checkout', methods=['GET', 'POST'])
@login_required
def checkout(appointment_id):
    """Pantalla de Caja para un turno especifico"""

    appointment = Appointment.query.get_or_404(appointment_id)
    form = CheckoutForm()
    
    # Cargar opciones de servicios y adicionales
    services = Service.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    
    # Configurar choices del formulario
    form.service_id.choices = [(s.id, f"{s.name} - ${s.base_price:,.0f}") for s in services]
    # Items con precio para mostrar en el formulario (aunque usaremos JS para el cálculo dinámico visual)
    form.item_ids.choices = [(i.id, f"{i.name} (+${i.price:,.0f})") for i in items]

    # Pre-popular datos en GET
    if request.method == 'GET':
        form.service_id.data = appointment.service_id
        form.item_ids.data = [i.id for i in appointment.items] # Pre-seleccionar items actuales
        
        # Si final_price es 0, usamos total_amount (precio calculado)
        current_total = appointment.final_price if appointment.final_price > 0 else appointment.total_amount
        form.final_price.data = int(current_total)
        
        # El monto a pagar por defecto es el saldo pendiente (basado en el precio actual)
        saldo = appointment.saldo_pendiente 
        form.amount.data = int(saldo) if saldo > 0 else 0

    if form.validate_on_submit():
        # 1. Actualizar datos del turno
        appointment.service_id = form.service_id.data
        
        # Actualizar Items (relación many-to-many)
        if form.item_ids.data:
            selected_items = Item.query.filter(Item.id.in_(form.item_ids.data)).all()
            appointment.items = selected_items
        else:
            appointment.items = []

        new_total = form.final_price.data
        
        # Actualizamos tanto final_price como total_amount para mantener coherencia
        # En este modelo flexible, el valor ingresado es la "Deuda Total"
        appointment.final_price = new_total
        appointment.total_amount = new_total 
        
        # 2. Registrar el Pago
        amount_paid = form.amount.data
        
        new_payment = Payment(
            appointment_id=appointment_id,
            amount=amount_paid,
            payment_method=form.payment_method.data,
            payment_type=form.payment_type.data,
            notes=form.notes.data
        )
        db.session.add(new_payment)

        # 3. Actualizar Estado (Usando el nuevo precio total para calcular saldo)
        # Recalculamos saldo pendiente con el nuevo total
        # saldo_pendiente property usa total_amount - pagos
        # Como aún no hacemos commit, los pagos viejos están en DB, el nuevo en session??
        # SQLAlchemy session trackea new_payment, asi que appointment.payments lo incluirá tras flush o manualmente
        
        db.session.flush() # Para que el nuevo pago cuente en las relaciones si es necesario, aunque saldo_pendiente es logica python
        
        if appointment.saldo_pendiente <= 0:
            appointment.status = 'Cobrado'
            
            # Calcular comisión sobre el PRECIO FINAL real cobrado
            prof = appointment.professional
            if prof:
                pct = prof.commission_percentage
                # Comisión sobre el total del servicio
                appointment.commission_amount = appointment.final_price * (pct / 100)
                
        elif appointment.status == 'Pendiente':
            appointment.status = 'Señado'
            
        db.session.commit()

        flash(f'Actualizado y pago de ${amount_paid:,.0f} registrado.')
        return redirect(url_for('main.checkout', appointment_id=appointment.id))

    # Datos para JavaScript
    import json
    services_json = json.dumps({s.id: s.base_price for s in services})
    items_json = json.dumps({i.id: i.price for i in items})
    
    # Total ya pagado (para el recibo)
    total_pagado = sum(p.amount for p in appointment.payments)
    
    return render_template('sales/checkout.html', 
                           appointment=appointment, 
                           form=form, 
                           services=services, 
                           items=items, 
                           services_json=services_json,
                           items_json=items_json,
                           total_pagado=total_pagado)

@main.route('/sales')
@login_required
def daily_sales():
    """Reporte de Ventas del Día y Comisiones"""
    today = datetime.now().date()

    # Todos los pagos del día
    all_payments = Payment.query.filter(
        func.date(Payment.date) == today
    ).order_by(Payment.date.desc()).all()
    
    # Separar pagos de señas
    pagos = [p for p in all_payments if p.payment_type == 'Pago']
    senas = [p for p in all_payments if p.payment_type == 'Seña']
    
    # Totales
    total_pagos = sum(p.amount for p in pagos)
    total_senas = sum(p.amount for p in senas)
    total_cash = total_pagos + total_senas

    # Turnos cobrados hoy (para comisiones)
    completed_appointments = Appointment.query.filter(
        func.date(Appointment.end_time) == today,
        Appointment.status == 'Cobrado'
    ).all()
    
    # Total comisiones
    total_comisiones = sum(a.commission_amount or 0 for a in completed_appointments)
    
    # Formulario vacío para CSRF token
    form = CheckoutForm()

    return render_template('sales/daily_report.html', 
                           pagos=pagos,
                           senas=senas,
                           total_pagos=total_pagos,
                           total_senas=total_senas,
                           total_cash=total_cash,
                           appointments=completed_appointments,
                           total_comisiones=total_comisiones,
                           form=form,
                           today=today)

@main.route('/payments/delete/<int:payment_id>', methods=['POST'])
@login_required
def delete_payment(payment_id):
    """Eliminar un pago (seña o pago)"""
    payment = Payment.query.get_or_404(payment_id)
    appointment = payment.appointment
    
    # Guardar datos para el mensaje
    amount = payment.amount
    payment_type = payment.payment_type
    
    # Eliminar el pago
    db.session.delete(payment)
    
    # Recalcular estado del turno
    # Si no hay más pagos, volver a Pendiente
    # Si hay pagos pero no cubre el total, poner Señado
    remaining_payments = [p for p in appointment.payments if p.id != payment_id]
    total_pagado_ahora = sum(p.amount for p in remaining_payments)
    
    if total_pagado_ahora <= 0:
        appointment.status = 'Pendiente'
    elif total_pagado_ahora < appointment.final_price:
        appointment.status = 'Señado'
    else:
        appointment.status = 'Cobrado'
    
    db.session.commit()
    
    flash(f'{payment_type} de ${amount:,.0f} eliminado.')
    return redirect(url_for('main.daily_sales'))