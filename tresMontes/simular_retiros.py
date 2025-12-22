#!/usr/bin/env python3
"""
Script para simular retiros de cajas de manera aleatoria
Uso: python3 manage.py shell < simular_retiros.py
O desde el shell de Django: exec(open('simular_retiros.py').read())
"""
import random
from django.contrib.auth.models import User
from django.utils import timezone
from registroCajas.models import Campana, Beneficiario, Retiro

def simular_retiros(cantidad=15):
    """
    Simula la entrega/retiro de cajas para beneficiarios aleatorios

    Args:
        cantidad: Número de retiros a simular (por defecto 15)
    """
    print(f"\n{'='*60}")
    print(f"SIMULANDO {cantidad} RETIROS DE CAJAS")
    print(f"{'='*60}\n")

    # Obtener campaña activa
    campana_activa = Campana.objects.filter(activa=True).first()

    if not campana_activa:
        print("❌ ERROR: No hay ninguna campaña activa")
        print("   Por favor, crea una campaña primero")
        return

    print(f"📦 Campaña activa: {campana_activa.nombre}")
    print(f"   Fecha: {campana_activa.fecha_inicio} a {campana_activa.fecha_fin}")
    print(f"   Planta: {campana_activa.planta.nombre}\n")

    # Obtener beneficiarios que NO han retirado aún
    beneficiarios_pendientes = Beneficiario.objects.filter(
        campana=campana_activa,
        retiro__isnull=True
    )

    total_pendientes = beneficiarios_pendientes.count()
    print(f"👥 Total beneficiarios pendientes: {total_pendientes}")

    if total_pendientes == 0:
        print("❌ ERROR: No hay beneficiarios pendientes de retiro")
        return

    # Ajustar cantidad si es mayor a los pendientes
    if cantidad > total_pendientes:
        print(f"⚠️  AVISO: Solo hay {total_pendientes} beneficiarios pendientes")
        cantidad = total_pendientes
        print(f"   Se simularán {cantidad} retiros\n")

    # Seleccionar beneficiarios aleatorios
    beneficiarios_seleccionados = random.sample(list(beneficiarios_pendientes), cantidad)

    # Obtener un usuario para asignar como confirmador (guardia o admin)
    usuario_confirmador = User.objects.filter(
        perfil__rol__in=['guardia', 'admin']
    ).first()

    if not usuario_confirmador:
        # Si no hay guardia/admin, usar cualquier usuario
        usuario_confirmador = User.objects.first()

    if not usuario_confirmador:
        print("❌ ERROR: No hay usuarios en el sistema")
        return

    print(f"👤 Usuario confirmador: {usuario_confirmador.get_full_name() or usuario_confirmador.username}")
    print(f"   Rol: {usuario_confirmador.perfil.get_rol_display() if hasattr(usuario_confirmador, 'perfil') else 'N/A'}\n")
    print(f"{'='*60}")
    print("PROCESANDO RETIROS...")
    print(f"{'='*60}\n")

    retiros_creados = 0

    for i, beneficiario in enumerate(beneficiarios_seleccionados, 1):
        try:
            # Crear el retiro
            retiro = Retiro.objects.create(
                beneficiario=beneficiario,
                confirmado_por=usuario_confirmador,
                fecha_hora=timezone.now(),
                observaciones=f"Retiro simulado automáticamente",
                retirado_por_tercero=False
            )

            retiros_creados += 1

            print(f"✅ [{i}/{cantidad}] {beneficiario.nombre}")
            print(f"    RUT: {beneficiario.rut}")
            print(f"    Código Caja: {beneficiario.codigo_caja}")
            print(f"    Tipo: {beneficiario.get_tipo_contrato_display()}")
            print(f"    Caja: {beneficiario.get_tipo_caja_display()}")
            print(f"    Planta: {beneficiario.planta.nombre}")
            print(f"    Fecha retiro: {retiro.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
            print()

        except Exception as e:
            print(f"❌ [{i}/{cantidad}] ERROR al crear retiro para {beneficiario.nombre}")
            print(f"    Error: {str(e)}\n")

    print(f"{'='*60}")
    print(f"RESUMEN")
    print(f"{'='*60}\n")
    print(f"✅ Retiros creados exitosamente: {retiros_creados}/{cantidad}")
    print(f"📊 Estadísticas de la campaña:")
    print(f"   - Total beneficiarios: {campana_activa.total_beneficiarios()}")
    print(f"   - Total entregados: {campana_activa.total_entregados()}")
    print(f"   - Total pendientes: {campana_activa.total_pendientes()}")
    print(f"   - Tasa de entrega: {campana_activa.tasa_entrega()}%")
    print(f"\n{'='*60}\n")

# Ejecutar la simulación
if __name__ == "__main__":
    # Cambiar el número aquí para simular más o menos retiros
    simular_retiros(15)
