from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login exitoso
            login(request, user)
            return redirect('panel_principal')
        else:
            # Credenciales inválidas
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'registroCajas/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login')


# @login_required
def panel_principal(request):
    # Datos de ejemplo
    context = {
        'entregas_hoy': 42,
        'pendientes': 8,
        'entregas_recientes': [
            {'nombre': 'Juan Perez', 'estado': 'entregado'},
            {'nombre': 'María González', 'estado': 'pendiente'},
        ]
    }
    return render(request, 'registroCajas/panel_principal.html', context)