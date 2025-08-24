# Copilot Instructions for AI Agents

## Project Overview
This is a Flask-based web application for managing a dog grooming business. The main entry point is `app.py`, which contains all routes, models, and logic. Data is stored in a SQLite database (`instance/peluqueria.db`).

## Architecture & Data Flow
- **Single-file Flask app**: All routes, models, and business logic are in `app.py`.
- **Templates**: HTML files are in the `templates/` directory. Each route renders a specific template (e.g., `menu.html`, `index.html`, `turnos.html`, etc.).
- **Database**: Uses SQLAlchemy ORM. Models: `Dog`, `Appointment`, `MedicalNote`. All database migrations and schema changes are handled via `db.create_all()` in `app.py`.
- **Soft Delete**: Both `Dog` and `Appointment` models use an `is_deleted` boolean for soft deletion. Deleted appointments can be restored or permanently deleted.
- **Backup**: Appointment data is periodically backed up to `export/turnosBackup.csv` via the `guardarBackUpTurnos()` function.

## Developer Workflows
- **Run the app**: `python app.py` (no build step required)
- **Dependencies**: Install with `pip install flask flask_sqlalchemy`
- **Database**: Automatically initialized if missing. No migration scripts; update models directly in `app.py`.
- **Debugging**: Use Flask's built-in debug mode (`debug=True` in `app.run`).
- **Testing**: No test files or framework detected. Manual testing via browser recommended.

## Project-Specific Patterns
- **Soft delete pattern**: Always use `is_deleted` for removing records. Do not physically delete unless using permanent delete routes.
- **Appointment conflict checking**: When creating or editing appointments, check for time conflicts with other appointments for the same dog.
- **Backup on appointment change**: Any change to appointments triggers a CSV backup.
- **Medical notes**: Linked to dogs via `MedicalNote` model and managed through `/add_note` route.

## Integration Points
- **External dependencies**: Flask, Flask-SQLAlchemy, CSV (Python stdlib)
- **No external APIs or services**
- **No authentication/authorization**

## Key Files & Directories
- `app.py`: Main application logic, models, routes
- `templates/`: HTML templates for all views
- `export/turnosBackup.csv`: CSV backup of appointments
- `instance/peluqueria.db`: SQLite database

## Example Patterns
- **Soft delete**:
  ```python
  dog.is_deleted = True
  db.session.commit()
  ```
- **Appointment conflict check**:
  ```python
  conflict = Appointment.query.filter(
      Appointment.dog_id == dog_id,
      Appointment.start_time < end_time,
      Appointment.end_time > start_time,
      Appointment.is_deleted == False
  ).first()
  ```
- **Backup after appointment change**:
  ```python
  guardarBackUpTurnos()
  ```

## Conventions
- All business logic is in `app.py`.
- Use SQLAlchemy ORM for all DB access.
- Use Flask's `render_template` for HTML views.
- Use soft delete for all deletions unless explicitly permanent.

---

If any section is unclear or missing, please provide feedback to improve these instructions.
