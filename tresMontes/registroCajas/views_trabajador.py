"""
Vistas del módulo Trabajador
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .decorators import trabajador_required
from .models import Planta, Beneficiario


@trabajador_required
def trabajador_home(request):
    """Vista principal del trabajador - ver estado de su caja"""
    perfil = request.user.perfil
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo) if planta_codigo else None

    # Buscar si el trabajador tiene una caja asignada en campaña activa
    beneficiario = None
    if perfil.rut:
        # Buscar en campañas activas de la planta
        beneficiario = Beneficiario.objects.filter(
            rut=perfil.rut,
            campana__planta=planta,
            campana__activa=True
        ).first()

    context = {
        'perfil': perfil,
        'planta': planta,
        'beneficiario': beneficiario,
    }

    return render(request, 'registroCajas/trabajador/home.html', context)
