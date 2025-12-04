from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel/', views.panel_principal, name='panel_principal'),
    path('buscar/', views.buscar_trabajador, name='buscar_trabajador'),
    path('registrar/', views.registrar_entrega, name='registrar_entrega'),
    path('importar/', views.importar_trabajadores, name='importar_trabajadores'),
    path('reportes/', views.reportes, name='reportes'),
]