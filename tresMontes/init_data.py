#!/usr/bin/env python
"""
Script para inicializar datos de prueba en el sistema Tres Montes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tresMontes.settings')
django.setup()

from django.contrib.auth.models import User
from registroCajas.models import Planta, Perfil


def crear_plantas():
    """Crea las 3 plantas del sistema"""
    plantas_data = [
        {'codigo': 'casablanca', 'nombre': 'Casa Blanca'},
        {'codigo': 'valparaiso_bif', 'nombre': 'Valparaíso Planta BIF'},
        {'codigo': 'valparaiso_bic', 'nombre': 'Valparaíso Planta BIC'},
    ]

    plantas_creadas = []
    for data in plantas_data:
        planta, created = Planta.objects.get_or_create(
            codigo=data['codigo'],
            defaults={'nombre': data['nombre'], 'activa': True}
        )
        plantas_creadas.append(planta)
        print(f"{'✓ Creada' if created else '  Existe'}: Planta {planta.nombre}")

    return plantas_creadas


def crear_usuarios():
    """Crea usuarios de prueba para cada rol"""
    plantas = list(Planta.objects.all())

    usuarios_data = [
        # Administradores
        {
            'username': 'admin',
            'password': '123',
            'email': 'admin@tresmontes.cl',
            'first_name': 'Ana',
            'last_name': 'Administradora',
            'perfil': {
                'rol': 'admin',
                'planta': plantas[0],
                'rut': '11.111.111-1',
                'nombre_completo': 'Ana Administradora'
            }
        },
        # Guardias
        {
            'username': 'guardia',
            'password': '123',
            'email': 'guardia@tresmontes.cl',
            'first_name': 'Carlos',
            'last_name': 'Silva',
            'perfil': {
                'rol': 'guardia',
                'planta': plantas[1],
                'rut': '22.222.222-2',
                'nombre_completo': 'Carlos Silva'
            }
        },
        {
            'username': 'luis.fernandez',
            'password': '123',
            'email': 'luis.fernandez@tresmontes.cl',
            'first_name': 'Luis',
            'last_name': 'Fernández',
            'perfil': {
                'rol': 'guardia',
                'planta': plantas[0],
                'rut': '33.333.333-3',
                'nombre_completo': 'Luis Fernández'
            }
        },
        # Trabajadores
        {
            'username': 'trabajador',
            'password': '123',
            'email': 'trabajador@tresmontes.cl',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'perfil': {
                'rol': 'trabajador',
                'planta': plantas[1],
                'rut': '44.444.444-4',
                'nombre_completo': 'Juan Pérez'
            }
        },
        {
            'username': 'maria.gonzalez',
            'password': '123',
            'email': 'maria.gonzalez@tresmontes.cl',
            'first_name': 'María',
            'last_name': 'González',
            'perfil': {
                'rol': 'trabajador',
                'planta': plantas[0],
                'rut': '55.555.555-5',
                'nombre_completo': 'María González'
            }
        },
    ]

    for data in usuarios_data:
        perfil_data = data.pop('perfil')

        # Crear o actualizar usuario
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name']
            }
        )

        if created:
            user.set_password(data['password'])
            user.save()

        # Crear o actualizar perfil
        perfil, perfil_created = Perfil.objects.get_or_create(
            user=user,
            defaults=perfil_data
        )

        if not perfil_created:
            # Actualizar perfil existente
            for key, value in perfil_data.items():
                setattr(perfil, key, value)
            perfil.save()

        status = '✓ Creado' if created else '  Actualizado'
        print(f"{status}: {perfil.nombre_completo} ({perfil.get_rol_display()}) - user: {user.username}, pass: {data['password']}")


def main():
    print("=" * 60)
    print("Inicializando datos del sistema Tres Montes")
    print("=" * 60)

    print("\n1. Creando plantas...")
    crear_plantas()

    print("\n2. Creando usuarios de prueba...")
    crear_usuarios()

    print("\n" + "=" * 60)
    print("✓ Inicialización completada!")
    print("=" * 60)
    print("\nUsuarios disponibles para login:")
    print("  - admin / 123 (Administrador)")
    print("  - guardia / 123 (Guardia)")
    print("  - luis.fernandez / 123 (Guardia)")
    print("  - trabajador / 123 (Trabajador)")
    print("  - maria.gonzalez / 123 (Trabajador)")
    print("=" * 60)


if __name__ == '__main__':
    main()
