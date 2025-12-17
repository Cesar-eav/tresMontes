from django.contrib import admin
from .models import (
    Planta, Perfil, Campana, DiaBloquedo,
    Beneficiario, Retiro, AutorizacionTercero, AgendaRetiro
)


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre', 'codigo']


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'user', 'rol', 'planta', 'rut']
    list_filter = ['rol', 'planta']
    search_fields = ['nombre_completo', 'rut', 'user__username']


@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'planta', 'fecha_inicio', 'fecha_fin', 'activa', 'total_beneficiarios', 'tasa_entrega']
    list_filter = ['activa', 'planta', 'fecha_inicio']
    search_fields = ['nombre']
    date_hierarchy = 'fecha_inicio'


@admin.register(DiaBloquedo)
class DiaBloqueadoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'campana', 'motivo', 'bloqueado_por']
    list_filter = ['motivo', 'campana']
    date_hierarchy = 'fecha'


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'campana', 'planta', 'tipo_contrato', 'tipo_caja', 'tiene_retiro']
    list_filter = ['campana', 'planta', 'tipo_contrato', 'tipo_caja']
    search_fields = ['nombre', 'rut']


@admin.register(Retiro)
class RetiroAdmin(admin.ModelAdmin):
    list_display = ['beneficiario', 'codigo_caja', 'fecha_hora', 'confirmado_por', 'retirado_por_tercero']
    list_filter = ['fecha_hora', 'retirado_por_tercero']
    search_fields = ['beneficiario__nombre', 'beneficiario__rut', 'codigo_caja']
    date_hierarchy = 'fecha_hora'
    readonly_fields = ['codigo_caja']


@admin.register(AutorizacionTercero)
class AutorizacionTerceroAdmin(admin.ModelAdmin):
    list_display = ['beneficiario', 'nombre_tercero', 'rut_tercero', 'fecha_autorizada', 'activa']
    list_filter = ['activa', 'solo_una_vez']
    search_fields = ['beneficiario__nombre', 'nombre_tercero', 'rut_tercero']


@admin.register(AgendaRetiro)
class AgendaRetiroAdmin(admin.ModelAdmin):
    list_display = ['beneficiario', 'fecha_agendada', 'confirmado_hoy', 'fecha_confirmacion']
    list_filter = ['confirmado_hoy', 'fecha_agendada']
    search_fields = ['beneficiario__nombre']
