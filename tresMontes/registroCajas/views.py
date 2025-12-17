from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Planta, Perfil


# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validar campos obligatorios
        if not all([username, password]):
            messages.error(request, 'Usuario y contraseña son obligatorios')
            return render(request, 'registroCajas/login.html')

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar que el usuario tenga perfil
            try:
                perfil = user.perfil
            except Perfil.DoesNotExist:
                messages.error(request, 'Usuario sin perfil asignado. Contacte al administrador.')
                return render(request, 'registroCajas/login.html')

            # Verificar que tenga planta asignada
            if not perfil.planta:
                messages.error(request, 'Usuario sin planta asignada. Contacte al administrador.')
                return render(request, 'registroCajas/login.html')

            # Login exitoso
            login(request, user)

            # Guardar planta en sesión (obtenida del perfil)
            request.session['planta_codigo'] = perfil.planta.codigo

            # Redirigir según el rol (obtenido del perfil)
            if perfil.rol == 'admin':
                return redirect('admin_home')
            elif perfil.rol == 'guardia':
                return redirect('guardia_home')
            else:  # trabajador
                return redirect('trabajador_home')
        else:
            # Credenciales inválidas
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'registroCajas/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login')


# ==================== VISTAS ADMINISTRADOR ====================

from .decorators import admin_required
from django.utils import timezone

@admin_required
def admin_home(request):
    """Panel principal del administrador"""
    # Obtener la planta del admin para mostrarla, pero no para filtrar los datos principales
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    from .models import Campana, Retiro
    # Para el admin, buscar CUALQUIER campaña activa, no solo la de su planta.
    # La más reciente es la más relevante.
    campana_activa = Campana.objects.filter(activa=True).order_by('-fecha_creacion').first()

    context = {
        'planta': planta, # La planta del admin se sigue mostrando
        'campana_activa': campana_activa,
    }

    if campana_activa:
        # Estadísticas del día
        hoy = timezone.now().date()
        retiros_hoy = Retiro.objects.filter(
            beneficiario__campana=campana_activa,
            fecha_hora__date=hoy
        )

        context.update({
            'total_beneficiarios': campana_activa.total_beneficiarios(),
            'total_entregados': campana_activa.total_entregados(),
            'total_pendientes': campana_activa.total_pendientes(),
            'tasa_entrega': campana_activa.tasa_entrega(),
            'entregas_hoy': retiros_hoy.count(),
            'entregas_recientes': retiros_hoy.order_by('-fecha_hora')[:5],
        })

    return render(request, 'registroCajas/admin/home.html', context)


