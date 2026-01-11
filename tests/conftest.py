# tests/conftest.py
import pytest
from app import create_app
from extensions import db
from models import User

@pytest.fixture
def app():
    # 1. Fabricamos la app
    app = create_app()
    
    # 2. Configuración de prueba
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", 
        "WTF_CSRF_ENABLED": False
    })

    # 3. Crear base de datos temporal
    with app.app_context():
        db.create_all()
        # Usuario Admin para tests
        admin = User(username="admin", role="admin")
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()