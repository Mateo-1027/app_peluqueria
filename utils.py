
import os
import csv
from extensions import db
from models import Appointment

def guardarBackUpTurnos():
    """
    Exporta una lista de los turnos activos a un archivo CSV.
    Crea la carpeta 'export' si no existe.
    """
    # Define la ruta de la carpeta de exportación y crea si es necesario
    export_folder = 'export'
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    # Define la ruta completa del archivo de backup
    filepath = os.path.join(export_folder, 'turnosBackup.csv')
    
    # Consulta todos los turnos que no están marcados como eliminados
    appointments = Appointment.query.filter_by(is_deleted=False).all()

    # Escribe los datos en el archivo CSV
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
    print("Backup de turnos guardado exitosamente.")