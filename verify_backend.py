import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tresMontes.settings')
django.setup()

from django.contrib.auth.models import User
from registroCajas.models import Trabajador, Contrato, Entrega
from registroCajas.services import verificar_trabajador, registrar_entrega

def run_tests():
    print("--- Iniciando Pruebas de Backend ---")
    
    # 1. Setup Data
    print("\n1. Creando datos de prueba...")
    
    # Create Guard
    guardia, _ = User.objects.get_or_create(username='guardia_test')
    print(f"   Guardia creado: {guardia.username}")
    
    # Create Worker
    rut_test = "12345678-9"
    trabajador, created = Trabajador.objects.get_or_create(
        rut=rut_test,
        defaults={'nombre': 'Juan', 'apellido': 'Perez'}
    )
    print(f"   Trabajador creado: {trabajador}")
    
    # Create Contract
    Contrato.objects.filter(trabajador=trabajador).delete() # Clean previous
    contrato = Contrato.objects.create(
        trabajador=trabajador,
        tipo_caja='premium',
        fecha_inicio=timezone.now().date(),
        fecha_fin=timezone.now().date() + timedelta(days=30),
        activo=True
    )
    print(f"   Contrato creado: {contrato}")

    # 2. Test Verification
    print("\n2. Probando verificar_trabajador()...")
    resultado = verificar_trabajador(rut_test)
    if resultado['valid']:
        print("   ✅ Verificación Exitosa")
    else:
        print(f"   ❌ Falló verificación: {resultado.get('error')}")

    # 3. Test Delivery Registration
    print("\n3. Probando registrar_entrega() - Intento 1...")
    # Clean previous deliveries for today
    Entrega.objects.filter(trabajador=trabajador, fecha_entrega__date=timezone.now().date()).delete()
    
    res1 = registrar_entrega(rut_test, guardia)
    if res1['success']:
        print(f"   ✅ Entrega 1 registrada: {res1['message']} (Tipo: {res1['tipo_caja']})")
    else:
        print(f"   ❌ Falló Entrega 1: {res1['message']}")

    # 4. Test Duplicate Delivery
    print("\n4. Probando registrar_entrega() - Intento 2 (Duplicado)...")
    res2 = registrar_entrega(rut_test, guardia)
    if not res2['success']:
        print(f"   ✅ Bloqueo de duplicado exitoso: {res2['message']}")
    else:
        print(f"   ❌ Error: Permitió duplicado")

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Error fatal en pruebas: {e}")
