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
    
    # Agregar filtro personalizado para formatear números
    @app.template_filter('format_number')
    def format_number(value):
        """Formatea números con separador de miles"""
        return f"{value:,.0f}".replace(',', '.')
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Inicializar Flask-Migrate
    login_manager.login_view = "main.login"
    login_manager.login_message = "Debes iniciar sesión para ver esta página."

    # Importar y registrar rutas y modelos
    with app.app_context():
        from routes import main # Importa el blueprint de rutas
        from models import User, Dog, Appointment, MedicalNote, Service, ServiceCategory, ServiceSize, Item # Importa los modelos
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
        
        # Crear categorías de servicio si no existen
        if not ServiceCategory.query.first():
            categories = [
                ServiceCategory(name='Baño', description='Solo baño', display_order=1),
                ServiceCategory(name='Baño y Deslanado', description='Baño con deslanado', display_order=2),
                ServiceCategory(name='Baño y Corte', description='Baño completo con corte', display_order=3),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Categorías de servicio creadas.")
        
        # Crear tamaños de servicio si no existen
        if not ServiceSize.query.first():
            sizes = [
                ServiceSize(name='Chico', display_order=1),
                ServiceSize(name='Mediano', display_order=2),
                ServiceSize(name='Mediano/Grande', display_order=3),
                ServiceSize(name='Gigante', display_order=4),
            ]
            db.session.add_all(sizes)
            db.session.commit()
            print("Tamaños de servicio creados.")
        
        # Crear servicios (combinaciones de categoría × tamaño) si no existen
        if not Service.query.first():
            categories = ServiceCategory.query.order_by(ServiceCategory.display_order).all()
            sizes = ServiceSize.query.order_by(ServiceSize.display_order).all()
            
            # Matriz de precios [categoría][tamaño]
            prices = {
                'Baño': [8000, 10000, 12000, 15000],
                'Baño y Deslanado': [12000, 15000, 18000, 22000],
                'Baño y Corte': [15000, 18000, 22000, 28000],
            }
            
            # Matriz de duraciones [categoría][tamaño]
            durations = {
                'Baño': [30, 45, 60, 75],
                'Baño y Deslanado': [45, 60, 75, 90],
                'Baño y Corte': [60, 90, 120, 150],
            }
            
            services = []
            for category in categories:
                for i, size in enumerate(sizes):
                    service = Service(
                        category_id=category.id,
                        size_id=size.id,
                        base_price=prices[category.name][i],
                        duration_minutes=durations[category.name][i]
                    )
                    services.append(service)
            
            db.session.add_all(services)
            print(f"Servicios creados: {len(services)} combinaciones de categoría × tamaño.")
        
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