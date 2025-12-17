"""
Vistas del módulo Administrador
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from .decorators import admin_required, admin_or_guardia_required
from .models import (
    Planta, Perfil, Campana, DiaBloquedo,
    Beneficiario, Retiro, AutorizacionTercero
)
from .utils import validar_rut_chileno
import json
from datetime import datetime, timedelta


@admin_required
def admin_crear_campana(request):
    """Vista para crear una nueva carga de nómina"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', f'Entrega {timezone.now().strftime("%B %Y")}')
        planta_id = request.POST.get('planta')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        archivo_nomina = request.FILES.get('archivo_nomina')
        dias_bloqueados_str = request.POST.get('dias_bloqueados', '')

        # Validaciones
        if not all([fecha_inicio, fecha_fin, planta_id]):
            messages.error(request, 'Las fechas de inicio, fin y la planta son obligatorias')
            return redirect('admin_crear_campana')

        planta = get_object_or_404(Planta, id=planta_id)

        if not archivo_nomina:
            messages.error(request, 'Debe subir un archivo con la nómina de beneficiarios')
            return redirect('admin_crear_campana')

        # Convertir fechas
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
            return redirect('admin_crear_campana')

        if fecha_fin < fecha_inicio:
            messages.error(request, 'La fecha de fin debe ser posterior a la fecha de inicio')
            return redirect('admin_crear_campana')

        # Crear campaña SIN el archivo primero (lo procesamos antes)
        campana = Campana.objects.create(
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            planta=planta,
            activa=True,
            creado_por=request.user
        )

        # Procesar días bloqueados
        if dias_bloqueados_str:
            try:
                dias_bloqueados = json.loads(dias_bloqueados_str)
                for fecha_str in dias_bloqueados:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    DiaBloquedo.objects.create(
                        campana=campana,
                        fecha=fecha,
                        motivo='otro',
                        bloqueado_por=request.user
                    )
            except:
                pass

        # Procesar archivo de nómina ANTES de guardarlo (el puntero del archivo está en posición 0)
        try:
            from .utils import procesar_excel_nomina
            print(f"DEBUG: Iniciando procesamiento de archivo {archivo_nomina.name}")
            beneficiarios_creados = procesar_excel_nomina(archivo_nomina, campana, planta)
            print(f"DEBUG: Procesamiento completado. {beneficiarios_creados} beneficiarios creados")

            # Ahora sí guardar el archivo en la campaña (resetear puntero primero)
            archivo_nomina.seek(0)
            campana.archivo_nomina = archivo_nomina
            campana.save()

            messages.success(request, f'Carga creada exitosamente con {beneficiarios_creados} beneficiarios')
        except Exception as e:
            print(f"DEBUG: Error en procesamiento: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            campana.delete()  # Eliminar la campaña si hubo error
            return redirect('admin_crear_campana')

        return redirect('admin_home')

    # GET
    plantas = Planta.objects.filter(activa=True)
    # Obtener rango de fechas sugerido
    hoy = timezone.now().date()
    fecha_inicio_sugerida = hoy
    fecha_fin_sugerida = hoy + timedelta(days=30)

    context = {
        'plantas': plantas,
        'fecha_inicio_sugerida': fecha_inicio_sugerida,
        'fecha_fin_sugerida': fecha_fin_sugerida,
    }

    return render(request, 'registroCajas/admin/crear_campana.html', context)


@admin_required
def admin_usuarios(request):
    """Vista de gestión de usuarios"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Obtener todos los perfiles
    perfiles = Perfil.objects.select_related('user', 'planta').order_by('rol', 'nombre_completo')

    context = {
        'planta': planta,
        'perfiles': perfiles,
        'admin_count': perfiles.filter(rol='admin').count(),
        'guardia_count': perfiles.filter(rol='guardia').count(),
        'trabajador_count': perfiles.filter(rol='trabajador').count(),
    }

    return render(request, 'registroCajas/admin/usuarios.html', context)


@admin_required
def admin_crear_usuario(request):
    """Vista para crear un nuevo usuario (admin o guardia)"""
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        rol = request.POST.get('rol')
        planta_id = request.POST.get('planta')
        rut = request.POST.get('rut', '').strip()

        # Validaciones
        if not all([nombre_completo, username, password, rol, planta_id]):
            messages.error(request, 'Todos los campos son obligatorios')
            return redirect('admin_crear_usuario')

        if rol not in ['admin', 'guardia']:
            messages.error(request, 'Rol inválido')
            return redirect('admin_crear_usuario')

        # Verificar si el username ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return redirect('admin_crear_usuario')

        # Validar RUT si está presente
        if rut:
            es_valido, mensaje = validar_rut_chileno(rut)
            if not es_valido:
                messages.error(request, f'RUT inválido: {mensaje}')
                return redirect('admin_crear_usuario')
            
            # Verificar si el RUT ya existe
            if Perfil.objects.filter(rut=rut).exists():
                messages.error(request, 'El RUT ya está registrado')
                return redirect('admin_crear_usuario')

        try:
            planta = Planta.objects.get(id=planta_id)

            # Crear usuario
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=nombre_completo.split()[0] if nombre_completo.split() else nombre_completo,
                last_name=' '.join(nombre_completo.split()[1:]) if len(nombre_completo.split()) > 1 else ''
            )

            # Crear perfil
            Perfil.objects.create(
                user=user,
                rol=rol,
                planta=planta,
                rut=rut if rut else None,
                nombre_completo=nombre_completo
            )

            messages.success(request, f'Usuario {username} creado exitosamente')
            return redirect('admin_usuarios')

        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
            return redirect('admin_crear_usuario')

    # GET - mostrar formulario
    plantas = Planta.objects.filter(activa=True)
    context = {
        'plantas': plantas,
    }

    return render(request, 'registroCajas/admin/crear_usuario.html', context)


@admin_required
def admin_reportes(request):
    """Vista de reportes y estadísticas"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Filtros
    periodo = request.GET.get('periodo', 'hoy')

    # Calcular rango de fechas según período
    hoy = timezone.now().date()
    if periodo == 'hoy':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = hoy
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'anio':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    else:
        # Por defecto, si el periodo no es válido, mostrar 'hoy'
        periodo = 'hoy'
        fecha_inicio = hoy
        fecha_fin = hoy

    # Obtener campañas cuyo rango de fechas se solapa con el período seleccionado
    campanas = Campana.objects.filter(
        planta=planta,
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio
    ).prefetch_related('beneficiarios')

    # Total de beneficiarios de las campañas activas en el período
    total_beneficiarios = Beneficiario.objects.filter(campana__in=campanas).count()

    # Total de entregados para TODAS las campañas activas (para tasa de entrega y pendientes)
    total_entregados_historico = Retiro.objects.filter(beneficiario__campana__in=campanas).count()

    # Total de entregados EN EL PERÍODO seleccionado (para el card de "Entregados")
    total_entregados_periodo = Retiro.objects.filter(
        beneficiario__campana__in=campanas,
        fecha_hora__date__gte=fecha_inicio,
        fecha_hora__date__lte=fecha_fin
    ).count()
    
    # Los pendientes siempre son sobre el total
    total_pendientes = total_beneficiarios - total_entregados_historico
    
    # La tasa de entrega también es sobre el total
    tasa_entrega = round((total_entregados_historico / total_beneficiarios * 100) if total_beneficiarios > 0 else 0, 1)

    # Retiros recientes en el período para la lista
    retiros = Retiro.objects.filter(
        beneficiario__campana__in=campanas,
        fecha_hora__date__gte=fecha_inicio,
        fecha_hora__date__lte=fecha_fin
    ).select_related('beneficiario', 'confirmado_por')

    context = {
        'planta': planta,
        'periodo': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_beneficiarios': total_beneficiarios,
        'total_entregados': total_entregados_periodo, # <-- ESTE ES EL CAMBIO PRINCIPAL PARA LA UI
        'total_pendientes': total_pendientes,
        'tasa_entrega': tasa_entrega,
        'campanas': campanas,
        'retiros_recientes': retiros[:10],
    }

    return render(request, 'registroCajas/admin/reportes.html', context)


@admin_required
def admin_emergencia(request):
    """Vista del sistema de emergencia para bloquear días"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Obtener campaña activa
    campana_activa = Campana.objects.filter(planta=planta, activa=True).first()

    if request.method == 'POST':
        if not campana_activa:
            messages.error(request, 'No hay carga activa para bloquear días')
            return redirect('admin_emergencia')

        fecha_str = request.POST.get('fecha')
        motivo = request.POST.get('motivo', 'emergencia')
        descripcion = request.POST.get('descripcion', '')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-d').date()

            # Validar que la fecha esté dentro del rango de la carga
            if fecha < campana_activa.fecha_inicio or fecha > campana_activa.fecha_fin:
                messages.error(request, 'La fecha debe estar dentro del rango de la carga activa')
                return redirect('admin_emergencia')

            # Crear día bloqueado
            DiaBloquedo.objects.create(
                campana=campana_activa,
                fecha=fecha,
                motivo=motivo,
                descripcion=descripcion,
                bloqueado_por=request.user
            )

            messages.success(request, f'Día {fecha.strftime("%d/%m/%Y")} bloqueado exitosamente')
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
        except Exception as e:
            messages.error(request, f'Error al bloquear día: {str(e)}')

        return redirect('admin_emergencia')

    # GET - mostrar lista de días bloqueados
    dias_bloqueados = []
    if campana_activa:
        dias_bloqueados = campana_activa.dias_bloqueados.all().order_by('-fecha')

    context = {
        'planta': planta,
        'campana_activa': campana_activa,
        'dias_bloqueados': dias_bloqueados,
    }

    return render(request, 'registroCajas/admin/emergencia.html', context)


@admin_required
def admin_eliminar_bloqueo(request, bloqueo_id):
    """Eliminar un día bloqueado"""
    bloqueo = get_object_or_404(DiaBloquedo, id=bloqueo_id)

    # Para el admin, se elimina la restricción de planta
    # planta_codigo = request.session.get('planta_codigo')
    # if bloqueo.campana.planta.codigo != planta_codigo:
    #     messages.error(request, 'No tiene permisos para eliminar este bloqueo')
    #     return redirect('admin_emergencia')

    fecha = bloqueo.fecha
    bloqueo.delete()
    messages.success(request, f'Bloqueo del día {fecha.strftime("%d/%m/%Y")} eliminado')

    return redirect('admin_emergencia')


@admin_or_guardia_required
def lista_diaria(request):
    """Vista de lista diaria de entregas (compartida admin/guardia)"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Buscar CUALQUIER campaña activa
    campana_activa = Campana.objects.filter(activa=True).order_by('-fecha_creacion').first()

    if not campana_activa:
        context = {
            'planta': planta,
            'campana_activa': None,
        }
        return render(request, 'registroCajas/shared/lista_diaria.html', context)

    # Filtros
    filtro_fecha = request.GET.get('filtro_fecha', 'hoy')
    filtro_tipo = request.GET.get('filtro_tipo', 'todos')
    busqueda = request.GET.get('busqueda', '')

    # Si es admin, ve todos los beneficiarios de la campaña. Si es guardia, solo los de su planta.
    if request.user.perfil.rol == 'admin':
        beneficiarios = campana_activa.beneficiarios.all()
    else: # Guardia
        beneficiarios = campana_activa.beneficiarios.filter(planta=planta)


    # Filtrar por tipo de contrato
    if filtro_tipo != 'todos':
        beneficiarios = beneficiarios.filter(tipo_contrato=filtro_tipo)

    # Filtrar por búsqueda
    if busqueda:
        beneficiarios = beneficiarios.filter(
            Q(nombre__icontains=busqueda) | Q(rut__icontains=busqueda)
        )

    # Ordenar: primero entregados, luego pendientes
    beneficiarios_list = []
    for b in beneficiarios:
        beneficiarios_list.append({
            'beneficiario': b,
            'tiene_retiro': b.tiene_retiro(),
            'retiro': b.retiro if b.tiene_retiro() else None
        })

    # Ordenar: entregados primero
    beneficiarios_list.sort(key=lambda x: (not x['tiene_retiro'], x['beneficiario'].nombre))

    context = {
        'planta': planta,
        'campana_activa': campana_activa,
        'beneficiarios': beneficiarios_list,
        'total_beneficiarios': len(beneficiarios_list),
        'total_entregados': sum(1 for b in beneficiarios_list if b['tiene_retiro']),
        'total_pendientes': sum(1 for b in beneficiarios_list if not b['tiene_retiro']),
        'filtro_fecha': filtro_fecha,
        'filtro_tipo': filtro_tipo,
        'busqueda': busqueda,
    }

    return render(request, 'registroCajas/shared/lista_diaria.html', context)


@login_required
def perfil(request):
    """Vista de perfil de usuario (compartida por todos los roles)"""
    perfil = request.user.perfil
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo) if planta_codigo else None

    context = {
        'perfil': perfil,
        'planta': planta,
    }

    return render(request, 'registroCajas/shared/perfil.html', context)


@admin_required
def admin_gestionar_cargas(request):
    """Vista para ver y gestionar todas las cargas"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo) # Se mantiene para mostrar la planta del admin

    # Para el admin, obtener todas las campañas de TODAS las plantas
    campanas = Campana.objects.all().select_related('planta', 'creado_por__perfil').order_by('-fecha_inicio')

    # Agregar información de beneficiarios a cada campaña
    campanas_info = []
    for campana in campanas:
        campanas_info.append({
            'campana': campana,
            'total_beneficiarios': campana.total_beneficiarios(),
            'total_entregados': campana.total_entregados(),
            'total_pendientes': campana.total_pendientes(),
        })

    context = {
        'planta': planta, # La planta del admin se sigue mostrando
        'campanas_info': campanas_info,
    }

    return render(request, 'registroCajas/admin/gestionar_cargas.html', context)


@admin_required
def admin_eliminar_carga(request, campana_id):
    """Vista para eliminar una carga completa"""
    campana = get_object_or_404(Campana, id=campana_id)

    # Para el admin, se elimina la restricción de planta
    # planta_codigo = request.session.get('planta_codigo')
    # if campana.planta.codigo != planta_codigo:
    #     messages.error(request, 'No tiene permisos para eliminar esta carga')
    #     return redirect('admin_gestionar_cargas')

    if request.method == 'POST':
        nombre = campana.nombre
        total_benef = campana.total_beneficiarios()
        campana.delete()
        messages.success(request, f'Carga "{nombre}" eliminada exitosamente ({total_benef} beneficiarios)')
        return redirect('admin_gestionar_cargas')

    return redirect('admin_gestionar_cargas')


@admin_required
def admin_ver_detalle_carga(request, campana_id):
    """Vista para ver el detalle completo de una carga"""
    campana = get_object_or_404(Campana, id=campana_id)

    # Para el admin, se elimina la restricción de planta
    # La planta se obtiene de la campaña para consistencia
    planta = campana.planta

    # Obtener todos los beneficiarios
    beneficiarios = campana.beneficiarios.all().order_by('nombre')

    # Contar contratos por tipo
    contratos_indefinidos = beneficiarios.filter(tipo_contrato='indefinido').count()
    contratos_fijos = beneficiarios.filter(tipo_contrato='fijo').count()

    # Agrupar beneficiarios por planta
    beneficiarios_por_planta = {}
    for benef in beneficiarios:
        planta_nombre = benef.planta.nombre
        if planta_nombre not in beneficiarios_por_planta:
            beneficiarios_por_planta[planta_nombre] = {
                'planta_obj': benef.planta,
                'beneficiarios': [],
                'total': 0,
            }
        beneficiarios_por_planta[planta_nombre]['beneficiarios'].append(benef)
        beneficiarios_por_planta[planta_nombre]['total'] += 1

    context = {
        'planta': planta,
        'campana': campana,
        'beneficiarios': beneficiarios,
        'beneficiarios_por_planta': beneficiarios_por_planta,
        'contratos_indefinidos': contratos_indefinidos,
        'contratos_fijos': contratos_fijos,
        'total_beneficiarios': campana.total_beneficiarios(),
        'total_entregados': campana.total_entregados(),
        'total_pendientes': campana.total_pendientes(),
    }

    return render(request, 'registroCajas/admin/detalle_carga.html', context)
