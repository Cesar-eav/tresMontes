"""
Utilidades para el sistema de registro de cajas
"""
import openpyxl
import csv
import io
from .models import Beneficiario, Planta


def procesar_excel_nomina(archivo, campana, planta):
    """
    Procesa un archivo Excel o CSV con la nómina de beneficiarios

    Formato esperado:
    - Columna 1: Nombre completo
    - Columna 2: RUT (formato: 12.345.678-9)
    - Columna 3: Tipo de contrato (planta/contratista)
    - Columna 4 (opcional): Tipo de caja (estandar/especial/premium)

    Returns:
        int: Número de beneficiarios creados
    """
    try:
        # Detectar si es CSV o Excel
        nombre_archivo = archivo.name.lower()

        if nombre_archivo.endswith('.csv'):
            return _procesar_csv_nomina(archivo, campana, planta)
        else:
            return _procesar_excel_nomina(archivo, campana, planta)

    except Exception as e:
        raise Exception(f"Error al procesar archivo: {str(e)}")


def _procesar_csv_nomina(archivo, campana, planta):
    """
    Procesa un archivo CSV. Detecta automáticamente el formato:
    Formato 1: id,nombre,rut,tipo_contrato,tipo_caja,campana_id,planta_id
    Formato 2: RUT,EMPLEADO,NOMBRES,APELLIDOS,CARGO,TIPO DE CONTRATO,PERIODO,SEDE,ESTADO
    """
    beneficiarios_creados = 0
    filas_procesadas = 0
    errores = []

    try:
        # Leer el archivo CSV
        archivo_texto = archivo.read().decode('utf-8-sig')  # utf-8-sig maneja BOM
        print(f"DEBUG: Archivo leído, {len(archivo_texto)} caracteres")

        # Detectar delimitador (tabulador o coma)
        if '\t' in archivo_texto:
            lector_csv = csv.reader(io.StringIO(archivo_texto), delimiter='\t')
            print(f"DEBUG: Usando delimitador TABULADOR")
        else:
            lector_csv = csv.reader(io.StringIO(archivo_texto))
            print(f"DEBUG: Usando delimitador COMA")

        # Leer encabezado
        header = next(lector_csv, None)
        print(f"DEBUG: Encabezado CSV: {header}")
        print(f"DEBUG: Número de columnas en encabezado: {len(header) if header else 0}")

        if not header:
            raise Exception("El archivo CSV está vacío o no tiene encabezado")

        # Crear diccionario de índices de columnas
        header_lower = [h.strip().lower() if h else '' for h in header]
        indices = {}

        # Detectar formato del CSV basándose en el encabezado
        for i, col in enumerate(header_lower):
            if col == 'id':
                indices['id'] = i
            elif col in ['nombre', 'nombres']:
                indices['nombre'] = i
            elif col == 'rut':
                indices['rut'] = i
            elif col in ['tipo_contrato', 'tipo de contrato', 'contrato']:
                indices['tipo_contrato'] = i
            elif col in ['tipo_caja', 'tipo de caja', 'caja']:
                indices['tipo_caja'] = i
            elif col in ['planta_id', 'planta', 'sede', 'site']:
                indices['planta_id'] = i
            elif col in ['empleado']:
                indices['empleado'] = i
            elif col in ['apellidos', 'apellido']:
                indices['apellidos'] = i
            elif col in ['cargo']:
                indices['cargo'] = i
            elif col in ['estado']:
                indices['estado'] = i

        print(f"DEBUG: Índices detectados: {indices}")

        # Determinar formato
        formato_simple = 'nombre' in indices and 'rut' in indices
        print(f"DEBUG: Formato simple detectado: {formato_simple}")

        for idx, row in enumerate(lector_csv, start=2):
            filas_procesadas += 1
            print(f"DEBUG: Fila {idx}: {row}")
            print(f"DEBUG: Longitud de fila: {len(row)}")

            # Extraer datos según el formato detectado
            try:
                # Extraer RUT
                if 'rut' in indices:
                    rut = str(row[indices['rut']]).strip() if len(row) > indices['rut'] else ''
                else:
                    rut = str(row[0]).strip() if len(row) > 0 else ''

                if not rut:
                    error = f"Fila {idx}: RUT vacío"
                    print(f"DEBUG ERROR: {error}")
                    errores.append(error)
                    continue

                # Extraer nombre
                if 'nombre' in indices:
                    # Formato simple: nombre completo en una columna
                    nombre_completo = str(row[indices['nombre']]).strip()
                else:
                    # Formato extendido: construir desde empleado, nombres, apellidos
                    empleado = str(row[indices['empleado']]).strip() if 'empleado' in indices and len(row) > indices['empleado'] else ''
                    nombres = str(row[indices.get('nombre', 1)]).strip() if len(row) > indices.get('nombre', 1) else ''
                    apellidos = str(row[indices['apellidos']]).strip() if 'apellidos' in indices and len(row) > indices['apellidos'] else ''
                    partes_nombre = [p for p in [empleado, nombres, apellidos] if p]
                    nombre_completo = ' '.join(partes_nombre).strip()

                if not nombre_completo:
                    error = f"Fila {idx}: Nombre vacío"
                    print(f"DEBUG ERROR: {error}")
                    errores.append(error)
                    continue

                print(f"DEBUG: RUT={rut}, Nombre={nombre_completo}")

                # Extraer tipo de contrato
                if 'tipo_contrato' in indices:
                    tipo_contrato_raw = str(row[indices['tipo_contrato']]).strip().lower()
                else:
                    tipo_contrato_raw = 'indefinido'

                # Mapear tipos de contrato
                if tipo_contrato_raw in ['fijo', 'plazo fijo', 'contratista']:
                    tipo_contrato = 'fijo'
                else:
                    tipo_contrato = 'indefinido'

                print(f"DEBUG: Tipo contrato: {tipo_contrato}")

                # Extraer tipo de caja
                if 'tipo_caja' in indices:
                    tipo_caja = str(row[indices['tipo_caja']]).strip().lower()
                    if tipo_caja not in ['estandar', 'especial', 'premium', 'alternativa']:
                        tipo_caja = 'estandar'
                else:
                    tipo_caja = 'estandar'

                print(f"DEBUG: Tipo caja: {tipo_caja}")

                # Determinar planta por fila (si existe columna), sino usar la planta por defecto
                planta_por_fila = planta
                if 'planta_id' in indices and len(row) > indices['planta_id']:
                    raw_planta_val = str(row[indices['planta_id']]).strip()
                    print(f"DEBUG: Valor planta/sede del CSV: '{raw_planta_val}'")
                    if raw_planta_val:
                        # Intentar por ID numérico
                        try:
                            planta_id = int(raw_planta_val)
                            planta_por_fila = Planta.objects.get(id=planta_id)
                            print(f"DEBUG: Planta encontrada por ID {planta_id}: {planta_por_fila.nombre}")
                        except (ValueError, Planta.DoesNotExist):
                            # Si no es un ID numérico, mapear nombre/código a planta
                            raw_lower = raw_planta_val.lower()
                            planta_encontrada = False

                            # Mapeo de nombres comunes a códigos de planta
                            if 'santiago' in raw_lower or 'casablanca' in raw_lower:
                                try:
                                    planta_por_fila = Planta.objects.get(codigo='casablanca')
                                    print(f"DEBUG: Mapeado '{raw_planta_val}' -> Casa Blanca")
                                    planta_encontrada = True
                                except Planta.DoesNotExist:
                                    pass
                            elif 'valparaiso' in raw_lower or 'valparaíso' in raw_lower:
                                if 'bic' in raw_lower:
                                    try:
                                        planta_por_fila = Planta.objects.get(codigo='valparaiso_bic')
                                        print(f"DEBUG: Mapeado '{raw_planta_val}' -> Valparaíso BIC")
                                        planta_encontrada = True
                                    except Planta.DoesNotExist:
                                        pass
                                else:
                                    try:
                                        planta_por_fila = Planta.objects.get(codigo='valparaiso_bif')
                                        print(f"DEBUG: Mapeado '{raw_planta_val}' -> Valparaíso BIF")
                                        planta_encontrada = True
                                    except Planta.DoesNotExist:
                                        pass
                            elif 'rancagua' in raw_lower:
                                # Rancagua: buscar si existe alguna planta asociada
                                print(f"DEBUG: '{raw_planta_val}' (Rancagua) - usando planta por defecto")

                            # Si no se encontró por mapeo, intentar búsqueda directa
                            if not planta_encontrada:
                                try:
                                    planta_por_fila = Planta.objects.get(codigo=raw_lower)
                                    print(f"DEBUG: Planta encontrada por código: {planta_por_fila.nombre}")
                                except Planta.DoesNotExist:
                                    try:
                                        planta_por_fila = Planta.objects.get(nombre__iexact=raw_planta_val)
                                        print(f"DEBUG: Planta encontrada por nombre: {planta_por_fila.nombre}")
                                    except Planta.DoesNotExist:
                                        print(f"DEBUG: No se pudo mapear '{raw_planta_val}' - usando planta por defecto")

                print(f"DEBUG: Planta final: {planta_por_fila.nombre} (ID: {planta_por_fila.id})")

                # Crear beneficiario
                print(f"DEBUG: Creando beneficiario '{nombre_completo}' ({rut}) en planta '{planta_por_fila}'...")
                beneficiario, created = Beneficiario.objects.get_or_create(
                    campana=campana,
                    rut=rut,
                    defaults={
                        'nombre': nombre_completo,
                        'tipo_contrato': tipo_contrato,
                        'tipo_caja': tipo_caja,
                        'planta': planta_por_fila
                    }
                )

                if created:
                    beneficiarios_creados += 1
                    print(f"DEBUG: ✓ Beneficiario creado exitosamente")
                else:
                    print(f"DEBUG: ⚠ Beneficiario ya existía")

            except Exception as e:
                error = f"Fila {idx}: Error al procesar - {str(e)}"
                print(f"DEBUG ERROR: {error}")
                errores.append(error)

        print(f"DEBUG: ==========================================")
        print(f"DEBUG: RESUMEN FINAL")
        print(f"DEBUG: Filas procesadas: {filas_procesadas}")
        print(f"DEBUG: Beneficiarios creados: {beneficiarios_creados}")
        print(f"DEBUG: Errores: {len(errores)}")
        print(f"DEBUG: ==========================================")

        if errores:
            print(f"DEBUG: DETALLE DE ERRORES:")
            for error in errores:
                print(f"  - {error}")

    except Exception as e:
        print(f"DEBUG: !!!!! EXCEPCIÓN CAPTURADA !!!!!")
        print(f"DEBUG: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback completo:")
        print(traceback.format_exc())
        raise

    return beneficiarios_creados


def _procesar_excel_nomina(archivo, campana, planta):
    """Procesa un archivo Excel"""
    wb = openpyxl.load_workbook(archivo)
    ws = wb.active

    beneficiarios_creados = 0
    # Leer encabezado (fila 1) para intentar detectar columna de planta
    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    header_lower = [str(h).strip().lower() if h else '' for h in header_row]
    planta_idx = None
    for i, h in enumerate(header_lower):
        if any(k in h for k in ['planta', 'planta_id', 'sede', 'site', 'sucursal', 'centro']):
            planta_idx = i
            break
    print(f"DEBUG: Excel - índice de columna planta detectado: {planta_idx}")

    # Iterar desde la fila 2 (fila 1 es encabezado)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] or not row[1]:
            continue

        nombre = str(row[0]).strip()
        rut = str(row[1]).strip()
        tipo_contrato = str(row[2]).strip().lower() if row[2] else 'planta'
        tipo_caja = str(row[3]).strip().lower() if len(row) > 3 and row[3] else 'estandar'

        # Validar tipo de contrato
        if tipo_contrato not in ['planta', 'contratista']:
            tipo_contrato = 'planta'

        # Validar tipo de caja
        if tipo_caja not in ['estandar', 'especial', 'premium']:
            tipo_caja = 'estandar'

        # Determinar planta por fila (si existe columna), sino usar la planta por defecto
        planta_por_fila = planta
        try:
            if planta_idx is not None and len(row) > planta_idx:
                raw_planta_val = str(row[planta_idx]).strip() if row[planta_idx] is not None else ''
                if raw_planta_val:
                    try:
                        planta_por_fila = Planta.objects.get(id=int(raw_planta_val))
                    except Exception:
                        try:
                            planta_por_fila = Planta.objects.get(codigo=raw_planta_val)
                        except Exception:
                            try:
                                planta_por_fila = Planta.objects.get(nombre__iexact=raw_planta_val)
                            except Exception:
                                planta_por_fila = planta
        except Exception:
            planta_por_fila = planta

        # Crear beneficiario
        beneficiario, created = Beneficiario.objects.get_or_create(
            campana=campana,
            rut=rut,
            defaults={
                'nombre': nombre,
                'tipo_contrato': tipo_contrato,
                'tipo_caja': tipo_caja,
                'planta': planta_por_fila
            }
        )

        if created:
            beneficiarios_creados += 1

    return beneficiarios_creados


def generar_excel_entregados(campana):
    """
    Genera un archivo Excel con la lista de beneficiarios que retiraron

    Returns:
        Workbook: Archivo Excel generado
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Entregados"

    # Encabezados
    ws.append(['Nombre', 'RUT', 'Tipo Contrato', 'Tipo Caja', 'Fecha Retiro', 'Hora Retiro', 'Confirmado Por'])

    # Datos
    beneficiarios = campana.beneficiarios.filter(retiro__isnull=False).select_related('retiro', 'retiro__confirmado_por')

    for b in beneficiarios:
        retiro = b.retiro
        ws.append([
            b.nombre,
            b.rut,
            b.get_tipo_contrato_display(),
            b.get_tipo_caja_display(),
            retiro.fecha_hora.strftime('%d/%m/%Y'),
            retiro.fecha_hora.strftime('%H:%M'),
            retiro.confirmado_por.get_full_name() if retiro.confirmado_por else 'N/A'
        ])

    return wb


def generar_excel_no_retirados(campana):
    """
    Genera un archivo Excel con la lista de beneficiarios que NO retiraron

    Returns:
        Workbook: Archivo Excel generado
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "No Retirados"

    # Encabezados
    ws.append(['Nombre', 'RUT', 'Tipo Contrato', 'Tipo Caja'])

    # Datos
    beneficiarios = campana.beneficiarios.filter(retiro__isnull=True)

    for b in beneficiarios:
        ws.append([
            b.nombre,
            b.rut,
            b.get_tipo_contrato_display(),
            b.get_tipo_caja_display()
        ])

    return wb


def validar_rut_chileno(rut):
    """
    Valida si un RUT chileno es válido.
    
    Acepta formatos:
    - 12.345.678-9
    - 12345678-9
    - 12345678
    - 123456789
    
    Args:
        rut (str): RUT a validar
        
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    if not rut:
        return False, "RUT no puede estar vacío"
    
    # Limpiar RUT: remover espacios, puntos, convertir a mayúsculas
    rut_limpio = str(rut).strip().replace('.', '').replace('-', '').upper()
    
    # Validar que solo contenga dígitos y opcionalmente K al final
    if not rut_limpio:
        return False, "RUT inválido: vacío después de limpiar"
    
    if not (rut_limpio[:-1].isdigit() and (rut_limpio[-1].isdigit() or rut_limpio[-1] == 'K')):
        return False, "RUT inválido: contiene caracteres no permitidos"
    
    # Validar longitud (7-8 dígitos + 1 dígito verificador = 8-9 caracteres total)
    if len(rut_limpio) < 8 or len(rut_limpio) > 9:
        return False, f"RUT inválido: longitud incorrecta (se esperan 8-9 caracteres, se recibieron {len(rut_limpio)})"
    
    # Separar números y dígito verificador
    numeros = rut_limpio[:-1]
    digito_proporcionado = rut_limpio[-1]
    
    # Calcular dígito verificador correcto
    suma = 0
    multiplicador = 2
    
    # Iterar desde la derecha hacia la izquierda
    for i in range(len(numeros) - 1, -1, -1):
        suma += int(numeros[i]) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    # Calcular el dígito verificador
    digito_calculado = 11 - (suma % 11)
    
    if digito_calculado == 11:
        digito_calculado = '0'
    elif digito_calculado == 10:
        digito_calculado = 'K'
    else:
        digito_calculado = str(digito_calculado)
    
    # Comparar
    if digito_proporcionado != digito_calculado:
        return False, f"RUT inválido: dígito verificador incorrecto (esperado {digito_calculado}, recibido {digito_proporcionado})"
    
    return True, "RUT válido"

