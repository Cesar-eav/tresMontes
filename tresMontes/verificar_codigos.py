from registroCajas.models import Retiro

retiros = Retiro.objects.all()[:5]
print('=== CODIGOS DE CAJA GENERADOS ===\n')

for r in retiros:
    print(f'Beneficiario: {r.beneficiario.nombre}')
    print(f'Tipo Contrato: {r.beneficiario.tipo_contrato}')
    print(f'Codigo: {r.codigo_caja}')
    print(f'Fecha: {r.fecha_hora.strftime("%d/%m/%Y %H:%M")}\n')

print(f'Total de retiros: {Retiro.objects.count()}')
