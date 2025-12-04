import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tresMontes.settings')
django.setup()

from django.contrib.auth.models import User
from registroCajas.models import Trabajador, Contrato
from django.utils import timezone

def setup():
    # Crear superusuario si no existe
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superusuario creado: admin / admin123")
    else:
        print("Superusuario 'admin' ya existe")

    # Crear trabajador de prueba
    rut_demo = '11111111-1'
    if not Trabajador.objects.filter(rut=rut_demo).exists():
        t = Trabajador.objects.create(
            rut=rut_demo,
            nombre='Juan',
            apellido='Demo'
        )
        Contrato.objects.create(
            trabajador=t,
            tipo_caja='dieciochera',
            fecha_inicio=timezone.now().date()
        )
        print(f"Trabajador creado: {t} con contrato activo")
    else:
        print(f"Trabajador {rut_demo} ya existe")

if __name__ == '__main__':
    setup()
