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

    # Obtener campaña activa
    campana_activa = Campana.objects.filter(planta=planta, activa=True).first()

    # Calcular estadísticas filtradas por planta del guardia
    total_entregados = 0
    total_pendientes = 0
    if campana_activa:
        beneficiarios_planta = campana_activa.beneficiarios.filter(planta=planta)
        total_entregados = beneficiarios_planta.filter(retiro__isnull=False).distinct().count()
        total_pendientes = beneficiarios_planta.filter(retiro__isnull=True).count()

    context = {
        'planta': planta,
        'campana_activa': campana_activa,
        'total_entregados': total_entregados,
        'total_pendientes': total_pendientes,
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

    # Obtener campaña activa
    campana_activa = Campana.objects.filter(planta=planta, activa=True).first()

    beneficiario = None
    rut_buscado = request.GET.get('rut', '').strip()

    if rut_buscado and campana_activa:
        # Buscar beneficiario en la campaña activa
        try:
            beneficiario = Beneficiario.objects.get(
                rut=rut_buscado,
                campana=campana_activa
            )
        except Beneficiario.DoesNotExist:
            messages.error(request, f'No se encontró beneficiario con RUT {rut_buscado} en la carga activa')

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

    # Verificar que el beneficiario pertenece a la planta
    if beneficiario.campana.planta != planta:
        messages.error(request, 'El beneficiario no pertenece a esta planta')
        return redirect('guardia_home')

    # Verificar si ya tiene retiro
    if beneficiario.tiene_retiro():
        messages.warning(request, 'Esta caja ya fue entregada anteriormente')
        return redirect('guardia_buscar_rut')

    if request.method == 'POST':
        retira_titular = request.POST.get('retira_titular') == 'on'
        observaciones = request.POST.get('observaciones', '')

        # Crear retiro
        retiro = Retiro.objects.create(
            beneficiario=beneficiario,
            fecha_hora=timezone.now(),
            confirmado_por=request.user,
            observaciones=observaciones
        )

        # Si no retira el titular, crear autorización
        if not retira_titular:
            nombre_tercero = request.POST.get('nombre_tercero', '')
            rut_tercero = request.POST.get('rut_tercero', '')

            if nombre_tercero and rut_tercero:
                AutorizacionTercero.objects.create(
                    retiro=retiro,
                    nombre_tercero=nombre_tercero,
                    rut_tercero=rut_tercero,
                    autorizacion_verbal=True,
                    autorizado_por=request.user
                )

        messages.success(request, f'Entrega confirmada para {beneficiario.nombre}')
        return redirect('guardia_home')

    context = {
        'planta': planta,
        'beneficiario': beneficiario,
    }

    return render(request, 'registroCajas/guardia/confirmar.html', context)
