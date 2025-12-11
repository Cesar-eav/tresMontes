from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Planta, Perfil


# Create your views here.

def login_view(request):
    # Obtener todas las plantas para el selector
    plantas = Planta.objects.filter(activa=True)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')
        planta_codigo = request.POST.get('planta')

        # Validar campos obligatorios
        if not all([username, password, rol, planta_codigo]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'registroCajas/login.html', {'plantas': plantas})

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar que el usuario tenga perfil
            try:
                perfil = user.perfil
            except Perfil.DoesNotExist:
                messages.error(request, 'Usuario sin perfil asignado. Contacte al administrador.')
                return render(request, 'registroCajas/login.html', {'plantas': plantas})

            # Verificar que el rol coincida
            if perfil.rol != rol:
                messages.error(request, 'El rol seleccionado no coincide con su usuario')
                return render(request, 'registroCajas/login.html', {'plantas': plantas})

            # Verificar que la planta coincida (opcional para admins)
            if perfil.planta and perfil.planta.codigo != planta_codigo:
                messages.error(request, 'La planta seleccionada no coincide con su asignación')
                return render(request, 'registroCajas/login.html', {'plantas': plantas})

            # Login exitoso
            login(request, user)

            # Guardar planta en sesión
            request.session['planta_codigo'] = planta_codigo

            # Redirigir según el rol
            if perfil.rol == 'admin':
                return redirect('admin_home')
            elif perfil.rol == 'guardia':
                return redirect('guardia_home')
            else:  # trabajador
                return redirect('trabajador_home')
        else:
            # Credenciales inválidas
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'registroCajas/login.html', {'plantas': plantas})


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
    # Obtener campaña activa de la planta actual
    planta_codigo = request.session.get('planta_codigo')
    planta = get_object_or_404(Planta, codigo=planta_codigo)

    from .models import Campana, Retiro
    campana_activa = Campana.objects.filter(planta=planta, activa=True).first()

    context = {
        'planta': planta,
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


