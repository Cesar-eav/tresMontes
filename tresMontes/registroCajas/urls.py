from django.urls import path
from . import views
from . import views_admin
from . import views_guardia
from . import views_trabajador

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Administrador
    path('admin/home/', views.admin_home, name='admin_home'),
    path('admin/crear-campana/', views_admin.admin_crear_campana, name='admin_crear_campana'),
    path('admin/gestionar-cargas/', views_admin.admin_gestionar_cargas, name='admin_gestionar_cargas'),
    path('admin/eliminar-carga/<int:campana_id>/', views_admin.admin_eliminar_carga, name='admin_eliminar_carga'),
    path('admin/detalle-carga/<int:campana_id>/', views_admin.admin_ver_detalle_carga, name='admin_detalle_carga'),
    path('admin/usuarios/', views_admin.admin_usuarios, name='admin_usuarios'),
    path('admin/crear-usuario/', views_admin.admin_crear_usuario, name='admin_crear_usuario'),
    path('admin/editar-usuario/<int:perfil_id>/', views_admin.admin_editar_usuario, name='admin_editar_usuario'),
    path('admin/eliminar-usuario/<int:perfil_id>/', views_admin.admin_eliminar_usuario, name='admin_eliminar_usuario'),
    path('admin/reportes/', views_admin.admin_reportes, name='admin_reportes'),
    path('admin/emergencia/', views_admin.admin_emergencia, name='admin_emergencia'),
    path('admin/emergencia/eliminar/<int:bloqueo_id>/', views_admin.admin_eliminar_bloqueo, name='admin_eliminar_bloqueo'),

    # Guardia
    path('guardia/home/', views_guardia.guardia_home, name='guardia_home'),
    path('guardia/scanner/', views_guardia.guardia_scanner, name='guardia_scanner'),
    path('guardia/buscar-rut/', views_guardia.guardia_buscar_rut, name='guardia_buscar_rut'),
    path('guardia/confirmar/<int:beneficiario_id>/', views_guardia.guardia_confirmar, name='guardia_confirmar'),
    path('guardia/confirmar-exitoso/', views_guardia.guardia_confirmar_exitoso, name='guardia_confirmar_exitoso'),

    # Trabajador
    path('trabajador/home/', views_trabajador.trabajador_home, name='trabajador_home'),

    # Compartidas
    path('lista-diaria/', views_admin.lista_diaria, name='lista_diaria'),
    path('perfil/', views_admin.perfil, name='perfil'),
]