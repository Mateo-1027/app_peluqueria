from extensions import db  # Importa 'db'
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


#-------- Modelos --------#

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='peluquera')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Tabla intermedia para relación many-to-many entre Appointment e Item
appointment_items = db.Table('appointment_items',
    db.Column('appointment_id', db.Integer, db.ForeignKey('appointment.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True)
)

class ServiceCategory(db.Model):
    """Categorías de servicio (Baño, Baño y Deslanado, Baño y Corte, etc)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "Baño", "Baño y Corte", etc.
    description = db.Column(db.Text)  # Descripción de la categoría
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # Para ordenar en la UI

class ServiceSize(db.Model):
    """Tamaños de servicio (Chico, Mediano, Mediano/Grande, Gigante)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # "Chico", "Mediano", etc.
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # Para ordenar en la UI

class Service(db.Model):
    """Servicios = Categoría + Tamaño"""
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('service_size.id'), nullable=False)
    description = db.Column(db.Text)  # Descripción específica (opcional)
    base_price = db.Column(db.Float, nullable=False)  # Precio base del servicio
    duration_minutes = db.Column(db.Integer, default=60)  # Duración estimada
    is_active = db.Column(db.Boolean, default=True)  # Para ocultar servicios viejos
    
    # Relationships
    category = db.relationship('ServiceCategory', backref='services')
    size = db.relationship('ServiceSize', backref='services')
    
    @property
    def name(self):
        """Genera el nombre del servicio a partir de categoría y tamaño"""
        return f"{self.category.name} - {self.size.name}"

class Item(db.Model):
    """Items adicionales que se pueden agregar a un turno (Desanudado, Corte de uñas, etc)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "Desanudado"
    price = db.Column(db.Float, nullable=False)  # Precio del adicional
    is_active = db.Column(db.Boolean, default=True)  # Para ocultar items viejos

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100))
    owner_phone = db.Column(db.String(20))
    is_deleted = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)  # Notas adicionales del turno
    color = db.Column(db.String(20))
    is_deleted = db.Column(db.Boolean, default=False)
    
    
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))  # Servicio principal
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Peluquera que atiende
    status = db.Column(db.String(20), default='Pendiente')  # 'Pendiente', 'Finalizado', 'Cancelado'
    final_price = db.Column(db.Float)  # Precio final cobrado (se calcula al crear/editar)
    
    dog = db.relationship('Dog')
    service = db.relationship('Service')
    user = db.relationship('User')
    items = db.relationship('Item', secondary=appointment_items, backref='appointments')  # Items adicionales


class MedicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    dog = db.relationship('Dog')