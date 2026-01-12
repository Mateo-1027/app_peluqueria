# tests/conftest.py
import pytest
from app import create_app
from extensions import db
from models import User

@pytest.fixture
def app():
    # 1. Configuración de la App
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    # 2. Contexto de la Base de Datos
    with app.app_context():
        db.create_all()  # Crea las tablas
        
    
        # Verificamos si ya existe el usuario antes de crearlo para evitar el error
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("admin")
            db.session.add(admin)
            db.session.commit()

        yield app  # Aquí corren los tests

        # 3. Limpieza Total
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()