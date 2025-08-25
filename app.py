from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///peluqueria.db'
app.config['SECRET_KEY'] = 'clave-super-secreta'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"






#Back up
def guardarBackUpTurnos():

    filepath = os.path.join('export', 'turnosBackup.csv')
    appointments = Appointment.query.filter_by(is_deleted=False).all()

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Perro', 'Inicio', 'Fin', 'Descripcion'])
        for a in appointments:
            writer.writerow([
                a.id,
                a.dog.name,
                a.start_time.strftime('%Y-%m-%d %H:%M'),
                a.end_time.strftime('%Y-%m-%d %H:%M'),
                a.description or ''
            ])


# Inicializar DB si no exites
with app.app_context():
    db.create_all()

if __name__=='__main__':
    app.run(debug=True)


