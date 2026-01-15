# tests/test_checkout_integration.py
"""
Tests de Integración para el flujo de Checkout (Caja)
Estos tests verifican flujos completos: crear turno → seña → pago → eliminar
"""
import pytest
from models import (
    Dog, Owner, Service, ServiceCategory, ServiceSize, 
    Appointment, Payment, Professional, db
)
from datetime import datetime, timedelta


@pytest.fixture
def setup_data(app):
    """Crea datos base necesarios para los tests de checkout"""
    with app.app_context():
        # Crear Owner
        owner = Owner(name="Test Owner", phone="1234567890")
        db.session.add(owner)
        db.session.commit()
        
        # Crear Dog
        dog = Dog(name="Test Dog", owner_id=owner.id)
        db.session.add(dog)
        db.session.commit()
        
        # Crear ServiceCategory y ServiceSize
        category = ServiceCategory(name="Baño", display_order=1)
        db.session.add(category)
        db.session.commit()
        
        size = ServiceSize(name="Chico", display_order=1)
        db.session.add(size)
        db.session.commit()
        
        # Crear Service
        service = Service(
            category_id=category.id,
            size_id=size.id,
            base_price=20000,
            duration_minutes=60
        )
        db.session.add(service)
        db.session.commit()
        
        # Crear Professional
        prof = Professional(name="Test Peluquera", commission_percentage=50.0)
        db.session.add(prof)
        db.session.commit()
        
        # Crear Appointment
        start = datetime.now()
        end = start + timedelta(hours=1)
        
        appointment = Appointment(
            dog_id=dog.id,
            service_id=service.id,
            professional_id=prof.id,
            start_time=start,
            end_time=end,
            total_amount=20000,
            final_price=20000,
            status='Pendiente'
        )
        db.session.add(appointment)
        db.session.commit()
        
        return {
            'dog_id': dog.id,
            'owner_id': owner.id,
            'service_id': service.id,
            'professional_id': prof.id,
            'appointment_id': appointment.id
        }


def login(client):
    """Helper para loguearse"""
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)


class TestCheckoutFlow:
    """Tests para el flujo de checkout"""
    
    def test_checkout_page_loads(self, client, app, setup_data):
        """La página de checkout debe cargar correctamente"""
        login(client)
        
        with app.app_context():
            response = client.get(f'/appointments/{setup_data["appointment_id"]}/checkout')
            assert response.status_code == 200
            assert b'Resumen de Pago' in response.data
    
    def test_registrar_sena(self, client, app, setup_data):
        """Registrar una seña debe cambiar el estado a Señado"""
        login(client)
        
        with app.app_context():
            # Registrar seña de $5,000
            response = client.post(
                f'/appointments/{setup_data["appointment_id"]}/checkout',
                data={
                    'service_id': setup_data['service_id'],
                    'amount': 5000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Seña',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            # Verificar que el estado cambió a Señado
            appointment = Appointment.query.get(setup_data['appointment_id'])
            assert appointment.status == 'Señado'
            
            # Verificar que se registró el pago
            assert len(appointment.payments) == 1
            assert appointment.payments[0].amount == 5000
            assert appointment.payments[0].payment_type == 'Seña'
    
    def test_pago_completo(self, client, app, setup_data):
        """Pagar el total debe cambiar el estado a Cobrado"""
        login(client)
        
        with app.app_context():
            # Pagar el total de $20,000
            response = client.post(
                f'/appointments/{setup_data["appointment_id"]}/checkout',
                data={
                    'service_id': setup_data['service_id'],
                    'amount': 20000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Pago',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            # Verificar estado Cobrado
            appointment = Appointment.query.get(setup_data['appointment_id'])
            assert appointment.status == 'Cobrado'
            assert appointment.saldo_pendiente <= 0
    
    def test_sena_mas_pago(self, client, app, setup_data):
        """Seña + Pago posterior = Cobrado"""
        login(client)
        
        with app.app_context():
            appt_id = setup_data['appointment_id']
            service_id = setup_data['service_id']
            
            # 1. Registrar seña de $5,000
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': service_id,
                    'amount': 5000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Seña',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            # Verificar estado Señado
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Señado'
            assert appointment.saldo_pendiente == 15000
            
            # 2. Pagar el resto ($15,000)
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': service_id,
                    'amount': 15000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Pago',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            # Verificar estado Cobrado
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Cobrado'
            assert appointment.saldo_pendiente <= 0
            assert len(appointment.payments) == 2


class TestDeletePayment:
    """Tests para eliminar pagos"""
    
    def test_eliminar_pago_vuelve_a_pendiente(self, client, app, setup_data):
        """Al eliminar el único pago, el turno vuelve a Pendiente"""
        login(client)
        
        with app.app_context():
            appt_id = setup_data['appointment_id']
            
            # 1. Crear un pago
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': setup_data['service_id'],
                    'amount': 5000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Seña',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Señado'
            payment_id = appointment.payments[0].id
            
            # 2. Eliminar el pago
            response = client.post(
                f'/payments/delete/{payment_id}',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            # 3. Verificar que volvió a Pendiente
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Pendiente'
            assert len(appointment.payments) == 0
    
    def test_eliminar_pago_de_cobrado_vuelve_a_senado(self, client, app, setup_data):
        """Si elimino el último pago de un turno Cobrado, vuelve a Señado"""
        login(client)
        
        with app.app_context():
            appt_id = setup_data['appointment_id']
            service_id = setup_data['service_id']
            
            # 1. Seña de $5,000
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': service_id,
                    'amount': 5000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Seña',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            # 2. Pago del resto $15,000
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': service_id,
                    'amount': 15000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Pago',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Cobrado'
            
            # 3. Eliminar el último pago (el de $15,000)
            pago_id = [p for p in appointment.payments if p.payment_type == 'Pago'][0].id
            
            client.post(f'/payments/delete/{pago_id}', follow_redirects=True)
            
            # 4. Debe volver a Señado (queda la seña de $5,000)
            appointment = Appointment.query.get(appt_id)
            assert appointment.status == 'Señado'
            assert len(appointment.payments) == 1
            assert appointment.saldo_pendiente == 15000


class TestSaldoPendiente:
    """Tests para verificar el cálculo de saldo pendiente"""
    
    def test_saldo_pendiente_inicial(self, app, setup_data):
        """El saldo pendiente inicial debe ser igual al precio final"""
        with app.app_context():
            appointment = Appointment.query.get(setup_data['appointment_id'])
            assert appointment.saldo_pendiente == 20000
    
    def test_saldo_pendiente_despues_de_sena(self, client, app, setup_data):
        """El saldo pendiente debe reducirse después de una seña"""
        login(client)
        
        with app.app_context():
            appt_id = setup_data['appointment_id']
            
            # Seña de $5,000
            client.post(
                f'/appointments/{appt_id}/checkout',
                data={
                    'service_id': setup_data['service_id'],
                    'amount': 5000,
                    'payment_method': 'Efectivo',
                    'payment_type': 'Seña',
                    'final_price': 20000
                },
                follow_redirects=True
            )
            
            appointment = Appointment.query.get(appt_id)
            assert appointment.saldo_pendiente == 15000
