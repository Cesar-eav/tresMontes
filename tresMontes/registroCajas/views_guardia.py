"""
Vistas del módulo Guardia/Portería
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .decorators import admin_or_guardia_required
from .models import Planta, Campana, Beneficiario, Retiro, AutorizacionTercero


@admin_or_guardia_required
def guardia_home(request):
    """Vista principal del guardia"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Buscar CUALQUIER campaña activa
    campana_activa = Campana.objects.filter(activa=True).order_by('-fecha_creacion').first()

    total_entregados = 0
    total_pendientes = 0
    beneficiarios_pendientes = []

    if campana_activa:
        # Filtrar los beneficiarios de ESA campaña que pertenecen a la planta del guardia
        beneficiarios_planta = campana_activa.beneficiarios.filter(planta=planta)
        total_entregados = beneficiarios_planta.filter(retiro__isnull=False).distinct().count()
        total_pendientes = beneficiarios_planta.filter(retiro__isnull=True).count()
        beneficiarios_pendientes = beneficiarios_planta.filter(retiro__isnull=True).order_by('nombre')[:10]

    context = {
        'planta': planta,
        'campana_activa': campana_activa, # Puede ser una campaña de otra planta
        'total_entregados': total_entregados,
        'total_pendientes': total_pendientes,
        'beneficiarios_pendientes': beneficiarios_pendientes,
    }

    return render(request, 'registroCajas/guardia/home.html', context)


@admin_or_guardia_required
def guardia_scanner(request):
    """Vista del escáner QR"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    context = {
        'planta': planta,
    }

    return render(request, 'registroCajas/guardia/scanner.html', context)


@admin_or_guardia_required
def guardia_buscar_rut(request):
    """Vista para buscar beneficiario por RUT"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Obtener CUALQUIER campaña activa
    campana_activa = Campana.objects.filter(activa=True).order_by('-fecha_creacion').first()

    beneficiario = None
    rut_buscado = request.GET.get('rut', '').strip()
    desde_scanner = request.GET.get('auto', '') == '1'  # Parámetro para identificar escaneo QR

    if rut_buscado and campana_activa:
        # Buscar beneficiario en la campaña activa Y que pertenezca a la planta del guardia
        try:
            beneficiario = Beneficiario.objects.get(
                rut=rut_buscado,
                campana=campana_activa,
                planta=planta # Asegurar que el guardia solo pueda encontrar gente de su planta
            )

            # Si viene desde el scanner QR, registrar automáticamente
            if desde_scanner and beneficiario:
                # Verificar si ya tiene retiro
                if beneficiario.tiene_retiro():
                    messages.warning(request, f'La caja de {beneficiario.nombre} ya fue entregada anteriormente')
                    return redirect('guardia_scanner')

                # Crear retiro automáticamente
                retiro = Retiro.objects.create(
                    beneficiario=beneficiario,
                    fecha_hora=timezone.now(),
                    confirmado_por=request.user,
                    observaciones='Entrega registrada mediante escaneo QR'
                )

                # Guardar datos en sesión para el popup
                request.session['codigo_caja_entregada'] = retiro.codigo_caja
                request.session['nombre_beneficiario'] = beneficiario.nombre

                return redirect('guardia_confirmar_exitoso')

        except Beneficiario.DoesNotExist:
            messages.error(request, f'No se encontró beneficiario con RUT {rut_buscado} en la carga activa para esta planta')

    context = {
        'planta': planta,
        'campana_activa': campana_activa,
        'beneficiario': beneficiario,
        'rut_buscado': rut_buscado,
    }

    return render(request, 'registroCajas/guardia/buscar_rut.html', context)


@admin_or_guardia_required
def guardia_confirmar(request, beneficiario_id):
    """Vista para confirmar entrega de caja"""
    beneficiario = get_object_or_404(Beneficiario, id=beneficiario_id)
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Verificar que el beneficiario pertenece a la planta del guardia
    if beneficiario.planta != planta:
        messages.error(request, 'El beneficiario no pertenece a esta planta')
        return redirect('guardia_home')

    # Verificar si ya tiene retiro
    if beneficiario.tiene_retiro():
        messages.warning(request, 'Esta caja ya fue entregada anteriormente')
        return redirect('guardia_buscar_rut')

    if request.method == 'POST':
        retira_titular = request.POST.get('retira_titular') == 'on'
        observaciones = request.POST.get('observaciones', '').strip()

        # Si no retira el titular, validar datos del tercero
        if not retira_titular:
            nombre_tercero = request.POST.get('nombre_tercero', '').strip()
            rut_tercero = request.POST.get('rut_tercero', '').strip()

            if not nombre_tercero or not rut_tercero:
                messages.error(request, 'Debe ingresar el nombre y RUT de quien retira la caja')
                context = {
                    'planta': planta,
                    'beneficiario': beneficiario,
                }
                return render(request, 'registroCajas/guardia/confirmar.html', context)

        # Crear retiro
        retiro = Retiro.objects.create(
            beneficiario=beneficiario,
            fecha_hora=timezone.now(),
            confirmado_por=request.user,
            observaciones=observaciones
        )

        # Si no retira el titular, registrar datos del tercero
        if not retira_titular:
            retiro.retirado_por_tercero = True
            retiro.nombre_tercero = nombre_tercero
            retiro.rut_tercero = rut_tercero
            retiro.save()

            # Agregar información en observaciones para trazabilidad
            observacion_tercero = f"Retirado por: {nombre_tercero} (RUT: {rut_tercero})"
            if retiro.observaciones:
                retiro.observaciones = f"{retiro.observaciones}\n{observacion_tercero}"
            else:
                retiro.observaciones = observacion_tercero
            retiro.save()

        # Guardar el código de caja en la sesión para mostrarlo en el template
        request.session['codigo_caja_entregada'] = retiro.codigo_caja
        request.session['nombre_beneficiario'] = beneficiario.nombre

        # Si fue retirado por tercero, guardar también esta información
        if not retira_titular:
            request.session['retirado_por_tercero'] = True
            request.session['nombre_tercero'] = nombre_tercero
        else:
            request.session['retirado_por_tercero'] = False

        return redirect('guardia_confirmar_exitoso')

    context = {
        'planta': planta,
        'beneficiario': beneficiario,
    }

    return render(request, 'registroCajas/guardia/confirmar.html', context)


@admin_or_guardia_required
def guardia_confirmar_exitoso(request):
    """Vista de confirmación exitosa con código de caja"""
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    # Obtener datos de la sesión
    codigo_caja = request.session.pop('codigo_caja_entregada', None)
    nombre_beneficiario = request.session.pop('nombre_beneficiario', None)
    retirado_por_tercero = request.session.pop('retirado_por_tercero', False)
    nombre_tercero = request.session.pop('nombre_tercero', None)

    if not codigo_caja:
        return redirect('guardia_home')

    context = {
        'planta': planta,
        'codigo_caja': codigo_caja,
        'nombre_beneficiario': nombre_beneficiario,
        'retirado_por_tercero': retirado_por_tercero,
        'nombre_tercero': nombre_tercero,
    }

    return render(request, 'registroCajas/guardia/confirmar_exitoso.html', context)
