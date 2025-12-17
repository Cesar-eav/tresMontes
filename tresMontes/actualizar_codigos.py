from registroCajas.models import Retiro
from collections import defaultdict
import re

print('=== ACTUALIZANDO CODIGOS AL NUEVO FORMATO ===\n')

# Agrupar retiros por día y planta
retiros_por_dia_planta = defaultdict(list)

for retiro in Retiro.objects.all().order_by('fecha_hora'):
    fecha_key = retiro.fecha_hora.strftime('%d%m')
    planta_key = retiro.beneficiario.planta.get_codigo_corto()
    key = f"{fecha_key}_{planta_key}"
    retiros_por_dia_planta[key].append(retiro)

# Actualizar cada grupo con correlativos
total_actualizados = 0

for key, retiros in retiros_por_dia_planta.items():
    fecha_parte, planta_codigo = key.split('_')
    correlativo = 1

    for retiro in retiros:
        prefijo = 'I' if retiro.beneficiario.tipo_contrato == 'indefinido' else 'F'
        correlativo_str = str(correlativo).zfill(2)
        nuevo_codigo = f"{prefijo}-{fecha_parte}{planta_codigo}{correlativo_str}"

        print(f'{retiro.beneficiario.nombre}: {retiro.codigo_caja} -> {nuevo_codigo}')

        retiro.codigo_caja = nuevo_codigo
        retiro.save()

        correlativo += 1
        total_actualizados += 1

print(f'\nTotal de codigos actualizados: {total_actualizados}')
