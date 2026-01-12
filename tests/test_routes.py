
def test_home_page_redirect(client):
    """La raiz debe redirigir al login"""
    response = client.get('/')
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_login_page_loads(client):
    """La página de login debe cargar correctamente (Código 200)"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Iniciar" in response.data

def test_login_flow(client, app):
    """Prueba de inicio de sesión exitoso"""
    #Hacemos POST con las credenciales (creadas en conftest.py)
    response = client.post('/login', data={
        "username": "admin",
        "password": "admin"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Cerrar" in response.data or b"Bienvenido" in response.data