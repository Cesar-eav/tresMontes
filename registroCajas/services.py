from django.utils import timezone
from .models import Trabajador, Contrato, Entrega

def verificar_trabajador(rut):
    """
    Verifica si un trabajador existe y tiene contrato activo.
    Retorna un diccionario con el estado y los datos.
    """
    try:
        trabajador = Trabajador.objects.get(rut=rut)
        # Check for active contract
        # Un contrato es válido si activo=True y (fecha_fin es None o fecha_fin >= hoy)
        hoy = timezone.now().date()
        
        contratos = Contrato.objects.filter(trabajador=trabajador, activo=True)
        contrato_activo = None
        
        for contrato in contratos:
            if contrato.fecha_fin is None or contrato.fecha_fin >= hoy:
                contrato_activo = contrato
                break
        
        if contrato_activo:
             return {
                 "valid": True, 
                 "trabajador": trabajador, 
                 "contrato": contrato_activo,
                 "mensaje": f"Trabajador habilitado: {trabajador.nombre} {trabajador.apellido}"
             }
        else:
             return {
                 "valid": False, 
                 "error": "Trabajador sin contrato vigente",
                 "trabajador": trabajador
             }
             
    except Trabajador.DoesNotExist:
        return {"valid": False, "error": "RUT no encontrado en el sistema"}

def asignar_tipo_caja(trabajador):
    """
    Retorna el tipo de caja asignado al trabajador según su contrato activo.
    """
    verificacion = verificar_trabajador(trabajador.rut)
    if verificacion['valid']:
        return verificacion['contrato'].tipo_caja
    return None

def registrar_entrega(rut, usuario_guardia):
    """
    Registra la entrega de una caja si pasa todas las validaciones.
    """
    # 1. Verificar trabajador
    verificacion = verificar_trabajador(rut)
    if not verificacion['valid']:
        return {"success": False, "message": verificacion['error']}
    
    trabajador = verificacion['trabajador']
    contrato = verificacion['contrato']
    
    # 2. Validar duplicados (misma fecha)
    hoy = timezone.now().date()
    entrega_existente = Entrega.objects.filter(
        trabajador=trabajador,
        fecha_entrega__date=hoy
    ).exists()
    
    if entrega_existente:
        return {
            "success": False, 
            "message": f"ALERTA: El trabajador {trabajador.nombre} ya retiró su caja hoy."
        }
        
    # 3. Registrar entrega
    nueva_entrega = Entrega.objects.create(
        trabajador=trabajador,
        guardia=usuario_guardia
    )
    
    return {
        "success": True, 
        "message": "Entrega registrada exitosamente", 
        "tipo_caja": contrato.get_tipo_caja_display(),
        "entrega_id": nueva_entrega.id
    }
