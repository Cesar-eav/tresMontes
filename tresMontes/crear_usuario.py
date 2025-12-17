#!/usr/bin/env python3
"""
Script para crear usuarios manualmente desde línea de comandos
Uso: python3 crear_usuario.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tresMontes.settings')
sys.path.append('/var/www/html/tresMontes/tresMontes')
django.setup()

from django.contrib.auth.models import User
from registroCajas.models import Perfil, Planta


def crear_usuario():
    """Crear un nuevo usuario de forma interactiva"""
    print("=" * 60)
    print("CREAR NUEVO USUARIO - Sistema Tres Montes")
    print("=" * 60)

    # Mostrar plantas disponibles
    plantas = Planta.objects.filter(activa=True)
    print("\nPlantas disponibles:")
    for i, planta in enumerate(plantas, 1):
        print(f"  {i}. {planta.nombre} ({planta.codigo})")

    # Solicitar datos
    print("\n" + "-" * 60)
    nombre_completo = input("Nombre completo: ").strip()
    username = input("Usuario (login): ").strip()
    password = input("Contraseña: ").strip()
    email = input("Email (opcional): ").strip()
    rut = input("RUT (ej: 12.345.678-9, opcional): ").strip()

    print("\nRoles disponibles:")
    print("  1. Administrador")
    print("  2. Guardia / Portería")
    print("  3. Trabajador")
    rol_opcion = input("Seleccione rol (1-3): ").strip()

    rol_map = {
        '1': 'admin',
        '2': 'guardia',
        '3': 'trabajador'
    }
    rol = rol_map.get(rol_opcion)

    if not rol:
        print("❌ Rol inválido")
        return

    planta_opcion = input(f"Seleccione planta (1-{len(plantas)}): ").strip()
    try:
        planta = plantas[int(planta_opcion) - 1]
    except (ValueError, IndexError):
        print("❌ Planta inválida")
        return

    # Validaciones
    if not all([nombre_completo, username, password]):
        print("❌ Nombre, usuario y contraseña son obligatorios")
        return

    if User.objects.filter(username=username).exists():
        print(f"❌ El usuario '{username}' ya existe")
        return

    if rut and Perfil.objects.filter(rut=rut).exists():
        print(f"❌ El RUT '{rut}' ya está registrado")
        return

    # Crear usuario
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=nombre_completo.split()[0] if nombre_completo.split() else nombre_completo,
            last_name=' '.join(nombre_completo.split()[1:]) if len(nombre_completo.split()) > 1 else ''
        )

        # Crear perfil
        perfil = Perfil.objects.create(
            user=user,
            rol=rol,
            planta=planta,
            rut=rut if rut else None,
            nombre_completo=nombre_completo
        )

        print("\n" + "=" * 60)
        print("✅ Usuario creado exitosamente!")
        print("=" * 60)
        print(f"  Nombre: {nombre_completo}")
        print(f"  Usuario: {username}")
        print(f"  Contraseña: {password}")
        print(f"  Rol: {perfil.get_rol_display()}")
        print(f"  Planta: {planta.nombre}")
        if rut:
            print(f"  RUT: {rut}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error al crear usuario: {str(e)}")


if __name__ == '__main__':
    crear_usuario()
