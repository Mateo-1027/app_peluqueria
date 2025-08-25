from app import db 
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


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

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100))
    breed = db.Column(db.String(100))
    is_deleted = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(20))
    is_deleted = db.Column(db.Boolean, default=False)
    dog = db.relationship('Dog')


class MedicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    dog = db.relationship('Dog')