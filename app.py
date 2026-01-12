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
    

    # Filtro para formatear dinero
    @app.template_filter('format_number')
    def format_number(value):
        if value is None: return "0"
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
        from models import User, Professional, ServiceCategory, ServiceSize, Service, Item
        from utils import guardarBackUpTurnos # Importa las funciones de utilidad
        
        # Registrar el blueprint de rutas
        app.register_blueprint(main)
        
        # Inicializar DB y crear datos iniciales
        db.create_all()
        # 1. Crear Usuario Admin (Operador del sistema)
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print(">> Usuario 'admin' creado.")
        
        # 2. Crear Profesionales de Ejemplo (Peluqueros)
        if not Professional.query.first():
            profesionales = [
                Professional(name='Sandra', commission_percentage=50.0),
                Professional(name='Miguel', commission_percentage=45.0),
                Professional(name='Ayudante', commission_percentage=30.0),
            ]
            db.session.add_all(profesionales)
            db.session.commit()
            print(">> Profesionales iniciales creados.")

        # 3. Datos Maestros (Categorías, Tamaños, Items)
        if not ServiceCategory.query.first():
            # ... (Misma lógica de categorías que tenías antes) ...
            categories = [
                ServiceCategory(name='Baño', display_order=1),
                ServiceCategory(name='Baño y Corte', display_order=2),
                ServiceCategory(name='Corte Higiénico', display_order=3),
            ]
            db.session.add_all(categories)
            
            sizes = [
                ServiceSize(name='Chico', display_order=1),
                ServiceSize(name='Mediano', display_order=2),
                ServiceSize(name='Grande', display_order=3),
            ]
            db.session.add_all(sizes)
            
            items = [
                Item(name='Desanudado', price=2000),
                Item(name='Corte de Uñas', price=500),
            ]
            db.session.add_all(items)
            
            db.session.commit()
            print(">> Datos maestros creados.")
            
    return app

if __name__ == '__main__':
    my_app = create_app()
    my_app.run(debug=True)