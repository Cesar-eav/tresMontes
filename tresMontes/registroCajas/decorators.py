"""
Decoradores personalizados para control de acceso por roles
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(allowed_roles):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.

    Args:
        allowed_roles: Lista de roles permitidos ['admin', 'guardia', 'trabajador']

    Ejemplo:
        @role_required(['admin'])
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            try:
                perfil = request.user.perfil
                if perfil.rol in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'No tiene permisos para acceder a esta página. Rol requerido: {", ".join(allowed_roles)}')
                    # Redirigir al home según su rol
                    if perfil.rol == 'admin':
                        return redirect('admin_home')
                    elif perfil.rol == 'guardia':
                        return redirect('guardia_home')
                    else:
                        return redirect('trabajador_home')
            except AttributeError:
                messages.error(request, 'Usuario sin perfil asignado. Contacte al administrador.')
                return redirect('login')

        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorador para vistas exclusivas de administradores"""
    return role_required(['admin'])(view_func)


def guardia_required(view_func):
    """Decorador para vistas exclusivas de guardias"""
    return role_required(['guardia'])(view_func)


def trabajador_required(view_func):
    """Decorador para vistas exclusivas de trabajadores"""
    return role_required(['trabajador'])(view_func)


def admin_or_guardia_required(view_func):
    """Decorador para vistas accesibles por admin y guardia"""
    return role_required(['admin', 'guardia'])(view_func)
