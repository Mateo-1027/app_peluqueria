from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

#Formulario de Login

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')


class DogForm(FlaskForm):
    name = StringField('Nombre del Perro', validators=[DataRequired(), Length(max=100)])
    owner_name = StringField('Nombre del Dueño', validators=[Optional()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Mascota')

class AppointmentForm(FlaskForm):
    dog_id = SelectField('Perro', coerce=int, validators=[DataRequired()])
    description = StringField('Descripción', validators=[Optional(), Length(max=200)])
    start_time = DateTimeLocalField('Fecha y Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duration = IntegerField('Duracion (minutos)', validators=[DataRequired(), NumberRange(min=15, message="La duracion minima es de 15 minutos.")])
    color = StringField('Color', validators=[Optional()])
    ubmit = SubmitField('Guardar Turno')