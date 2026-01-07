from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, DateTimeLocalField, SelectMultipleField, RadioField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

#Formulario de Login

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')


class DogForm(FlaskForm):
    name = StringField('Nombre del Perro', validators=[DataRequired(), Length(max=100)])
    owner_name = StringField('Nombre del Dueño', validators=[Optional()])
    owner_phone = StringField('Teléfono del Dueño', validators=[Optional(), Length(max=20)])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Mascota')

class AppointmentForm(FlaskForm):
    dog_id = SelectField('Perro', coerce=int, validators=[DataRequired()])
    service_id = RadioField('Servicio', coerce=int, validators=[DataRequired()])  # RadioField para solo un servicio
    item_ids = SelectMultipleField('Adicionales (opcional)', coerce=int, validators=[Optional()])
    user_id = SelectField('Peluquera', coerce=int, validators=[DataRequired()])
    start_time = DateTimeLocalField('Fecha y Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duration = IntegerField('Duración (minutos)', validators=[DataRequired(), NumberRange(min=15, message="La duración mínima es de 15 minutos.")])  # Duración manual
    description = TextAreaField('Notas adicionales', validators=[Optional(), Length(max=500)])
    color = StringField('Color', validators=[Optional()])
    submit = SubmitField('Guardar Turno')

# Formularios para gestión de Servicios e Items
class ServiceForm(FlaskForm):
    category_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    size_id = SelectField('Tamaño', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Descripción', validators=[Optional()])
    base_price = IntegerField('Precio Base', validators=[DataRequired(), NumberRange(min=0)])
    duration_minutes = IntegerField('Duración Estimada (min)', validators=[Optional(), NumberRange(min=15)])
    is_active = SelectField('Estado', choices=[(1, 'Activo'), (0, 'Inactivo')], coerce=int)
    submit = SubmitField('Guardar Servicio')

class ServiceCategoryForm(FlaskForm):
    name = StringField('Nombre de la Categoría', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional()])
    display_order = IntegerField('Orden de Visualización', validators=[Optional(), NumberRange(min=0)])
    is_active = SelectField('Estado', choices=[(1, 'Activo'), (0, 'Inactivo')], coerce=int)
    submit = SubmitField('Guardar Categoría')

class ServiceSizeForm(FlaskForm):
    name = StringField('Nombre del Tamaño', validators=[DataRequired(), Length(max=50)])
    display_order = IntegerField('Orden de Visualización', validators=[Optional(), NumberRange(min=0)])
    is_active = SelectField('Estado', choices=[(1, 'Activo'), (0, 'Inactivo')], coerce=int)
    submit = SubmitField('Guardar Tamaño')

class ItemForm(FlaskForm):
    name = StringField('Nombre del Adicional', validators=[DataRequired(), Length(max=100)])
    price = IntegerField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    is_active = SelectField('Estado', choices=[(1, 'Activo'), (0, 'Inactivo')], coerce=int)
    submit = SubmitField('Guardar Adicional')
