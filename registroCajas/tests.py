from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Trabajador, Contrato, Entrega
from django.utils import timezone
import datetime

class PMVTests(TestCase):
    def setUp(self):
        # Crear guardia
        self.guardia = User.objects.create_user(username='guardia', password='password123')
        self.client = Client()
        
        # Crear trabajador
        self.trabajador = Trabajador.objects.create(
            rut='12345678-9',
            nombre='Juan',
            apellido='Perez'
        )
        
        # Crear contrato
        self.contrato = Contrato.objects.create(
            trabajador=self.trabajador,
            tipo_caja='dieciochera',
            fecha_inicio=timezone.now().date()
        )

    def test_login(self):
        response = self.client.post('/', {'username': 'guardia', 'password': 'password123'})
        self.assertRedirects(response, '/panel/')

    def test_buscar_trabajador_sin_login(self):
        response = self.client.post('/buscar/', {'rut': '12345678-9'})
        self.assertNotEqual(response.status_code, 200) # Debería redirigir a login

    def test_flujo_completo_entrega(self):
        self.client.login(username='guardia', password='password123')
        
        # 1. Buscar trabajador
        response = self.client.post('/buscar/', {'rut': '12345678-9'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Perez')
        self.assertContains(response, 'Caja Dieciochera')
        
        # 2. Registrar entrega
        response = self.client.post('/registrar/', {'rut': '12345678-9'})
        self.assertRedirects(response, '/panel/')
        
        # 3. Verificar que se creó la entrega
        entrega = Entrega.objects.filter(trabajador=self.trabajador).first()
        self.assertIsNotNone(entrega)
        self.assertEqual(entrega.guardia, self.guardia)
        
        # 4. Intentar registrar de nuevo (debe fallar/redirigir con error)
        response = self.client.post('/registrar/', {'rut': '12345678-9'})
        self.assertRedirects(response, '/panel/')
        # Verificar que sigue habiendo solo 1 entrega
        self.assertEqual(Entrega.objects.filter(trabajador=self.trabajador).count(), 1)
