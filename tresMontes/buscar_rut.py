from registroCajas.models import Beneficiario, Perfil, Campana
from django.contrib.auth.models import User

rut = '44.444.444-4'
print('=== BUSQUEDA DE RUT: 44.444.444-4 ===\n')

# Buscar en Perfil
perfil = Perfil.objects.filter(rut=rut).first()
if perfil:
    print('PERFIL ENCONTRADO:')
    print(f'  Nombre: {perfil.nombre_completo}')
    print(f'  Usuario: {perfil.user.username}')
    print(f'  Rol: {perfil.rol}')
    print(f'  Planta: {perfil.planta}\n')
else:
    print('No se encontro perfil\n')

# Buscar en Beneficiarios
beneficiarios = Beneficiario.objects.filter(rut=rut)
print(f'BENEFICIARIOS ({beneficiarios.count()}):')
if beneficiarios.exists():
    for b in beneficiarios:
        print(f'  - Campana: {b.campana.nombre}')
        print(f'    Planta: {b.planta.nombre}')
        print(f'    Activa: {b.campana.activa}')
        print(f'    Tiene retiro: {b.tiene_retiro()}')
        print(f'    ID: {b.id}\n')
else:
    print('  No se encontraron beneficiarios con este RUT')
