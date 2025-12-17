from registroCajas.models import Retiro, Beneficiario
from django.contrib.auth.models import User
from django.utils import timezone

# Obtener un beneficiario de prueba
beneficiario = Beneficiario.objects.filter(retiro__isnull=True).first()

if beneficiario:
    print(f'Beneficiario: {beneficiario.nombre}')
    print(f'Tipo Contrato: {beneficiario.tipo_contrato}')
    print(f'Planta: {beneficiario.planta.nombre} ({beneficiario.planta.get_codigo_corto()})')

    # Crear un retiro de prueba
    usuario = User.objects.filter(perfil__rol='guardia').first()

    retiro = Retiro(
        beneficiario=beneficiario,
        confirmado_por=usuario,
        observaciones='Prueba de nuevo formato de codigo'
    )

    # Generar el código
    codigo = retiro.generar_codigo_caja()
    print(f'\nCodigo generado: {codigo}')
    print(f'Formato: [I/F]-[DDMM][PLANTA][NN]')
    print(f'  I/F: {codigo[0]}')
    print(f'  DD: {codigo[2:4]} (dia)')
    print(f'  MM: {codigo[4:6]} (mes)')
    print(f'  Planta: {codigo[6:-2]}')
    print(f'  Correlativo: {codigo[-2:]}')

    # NO guardar, solo probar
    print('\n(No se guardo en la base de datos, solo prueba)')
else:
    print('No hay beneficiarios disponibles sin retiro')
