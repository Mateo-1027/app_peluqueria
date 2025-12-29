# app.py

from flask import Flask
from extensions import db, login_manager, migrate # Importa migrate también
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    # Inicializar la aplicación
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///peluqueria-db')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave-dev-por-defecto')
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Inicializar Flask-Migrate
    login_manager.login_view = "main.login"
    login_manager.login_message = "Debes iniciar sesión para ver esta página."

    # Importar y registrar rutas y modelos
    with app.app_context():
        from routes import main # Importa el blueprint de rutas
        from models import User, Dog, Appointment, MedicalNote, Service, Item # Importa los modelos
        from utils import guardarBackUpTurnos # Importa las funciones de utilidad
        
        # Registrar el blueprint de rutas
        app.register_blueprint(main)
        
        # Inicializar DB y crear datos iniciales
        db.create_all()
        
        # Crear usuario admin si no existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario 'admin' creado.")
        
        # Crear servicios básicos si no existen
        if not Service.query.first():
            services = [
                Service(name='Corte y Baño Pequeño', description='Para perros de hasta 10kg', 
                       base_price=15000, duration_minutes=60),
                Service(name='Corte y Baño Mediano', description='Para perros de 10-25kg',
                       base_price=18000, duration_minutes=90),
                Service(name='Corte y Baño Grande', description='Para perros de más de 25kg',
                       base_price=22000, duration_minutes=120),
                Service(name='Baño Simple', description='Solo baño sin corte',
                       base_price=10000, duration_minutes=45),
            ]
            db.session.add_all(services)
            print("Servicios básicos creados.")
        
        # Crear items adicionales si no existen
        if not Item.query.first():
            items = [
                Item(name='Desanudado', price=2000),
                Item(name='Corte de uñas', price=1500),
                Item(name='Limpieza de oídos', price=800),
                Item(name='Vaciado de glándulas', price=1200),
                Item(name='Shampoo especial', price=1000),
            ]
            db.session.add_all(items)
            print("Items adicionales creados.")
        
        db.session.commit()
            
    return app

if __name__ == '__main__':
    my_app = create_app()
    my_app.run(debug=True)