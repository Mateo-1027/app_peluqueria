# app.py

from flask import Flask
from extensions import db, login_manager # Importa las extensiones
from werkzeug.security import generate_password_hash, check_password_hash
import os

def create_app():
    # Inicializar la aplicación
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///peluqueria.db'
    app.config['SECRET_KEY'] = 'clave-super-secreta'
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # Importar y registrar rutas y modelos
    with app.app_context():
        from routes import main # Importa el blueprint de rutas
        from models import User, Dog, Appointment, MedicalNote # Importa los modelos
        from utils import guardarBackUpTurnos # Importa las funciones de utilidad
        
        # Registrar el blueprint de rutas
        app.register_blueprint(main)
        
        # Inicializar DB y crear usuario de ejemplo
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario 'admin' creado.")
            
    return app

if __name__ == '__main__':
    my_app = create_app()
    my_app.run(debug=True)