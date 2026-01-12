from extensions import db  # Importa 'db'
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# ==========================================
# 1. USUARIOS Y PERSONAL
# ==========================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='peluquera')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Professional(db.Model):
    """Peluquero/Estilista"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    commission = db.Column(db.Float, default=50.0)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship('Appointment', backref='professional', lazy=True)


# ==========================================
# 2. SERVICIOS Y PRODUCTOS
# ==========================================

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


# ==========================================
# 3. CLIENTES Y MASCOTAS
# ==========================================

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable= False)
    phone = db.Column(db.String(20), nullable = True)
    email = db.Column(db.String(100), nullable = True)
    address = db.Column(db.String(200), nullable=True)

    #Relacion con los perros
    dogs = db.relationship('Dog', backref='owner', lazy=True)


class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)

class MedicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    dog = db.relationship('Dog')


# ==========================================
# 4. GESTIÓN DE TURNOS Y VENTAS 
# ==========================================

class Appointment(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'))


    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    description = db.Column(db.Text)
    color = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pendiente') # 'Pendiente', 'Señado', 'Cobrado'
    is_deleted = db.Column(db.Boolean, default=False)

    # --- FINANZAS (VENTA) ---
    
    total_amount = db.Column(db.Float, default=0.0) 
    discount_type = db.Column(db.String(20), default='fijo') # 'fijo' o 'porcentaje'
    discount_value = db.Column(db.Float, default=0.0)
    final_price = db.Column(db.Float, default=0.0)
    commission_amount = db.Column(db.Float, default=0.0)

    dog = db.relationship('Dog')
    service = db.relationship('Service')
    items = db.relationship('Item', secondary=appointment_items, backref='appointments')
    payments = db.relationship('Payment', backref='appointment', lazy=True)

    @property
    def saldo_pendiente(self):
        """Calcula cuánto falta pagar"""
        pagado = sum(p.amount for p in self.payments)
        return self.final_price - pagado
    
class Payment(db.Model):
    """Caja: Registro de cada ingreso de dinero"""
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    
    # Efectivo, Transferencia, MercadoPago, Debito, Credito
    payment_method = db.Column(db.String(50), nullable=False) 
    
    # 'Seña' (Anticipo) o 'Pago' (Cancelación)
    payment_type = db.Column(db.String(20), default='Pago') 
    
    notes = db.Column(db.String(200))