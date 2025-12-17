from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import random
import string


# Validador de RUT chileno
rut_validator = RegexValidator(
    regex=r'^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]{1}$',
    message='Formato de RUT inválido. Use: 12.345.678-9'
)


class Planta(models.Model):
    """Plantas de Tres Montes"""
    PLANTAS_CHOICES = [
        ('casablanca', 'Casa Blanca'),
        ('valparaiso_bif', 'Valparaíso Planta BIF'),
        ('valparaiso_bic', 'Valparaíso Planta BIC'),
    ]

    codigo = models.CharField(max_length=50, unique=True, choices=PLANTAS_CHOICES)
    nombre = models.CharField(max_length=100)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'

    def __str__(self):
        return self.nombre

    def get_codigo_corto(self):
        """Retorna el código corto de la planta para el código de caja"""
        codigos = {
            'casablanca': 'CB',
            'valparaiso_bif': 'BIF',
            'valparaiso_bic': 'BIC',
        }
        return codigos.get(self.codigo, 'XXX')


class Perfil(models.Model):
    """Perfil extendido del usuario con rol y planta"""
    ROLES_CHOICES = [
        ('admin', 'Administrador'),
        ('guardia', 'Guardia / Portería'),
        ('trabajador', 'Trabajador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES)
    planta = models.ForeignKey(Planta, on_delete=models.SET_NULL, null=True, blank=True)
    rut = models.CharField(max_length=12, validators=[rut_validator], unique=True, null=True, blank=True)
    nombre_completo = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_rol_display()})"


class Campana(models.Model):
    """Campaña de entrega de cajas"""
    nombre = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE)
    activa = models.BooleanField(default=True)
    archivo_nomina = models.FileField(upload_to='nominas/', null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Campaña'
        verbose_name_plural = 'Campañas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} - {self.planta.nombre}"

    def total_beneficiarios(self):
        return self.beneficiarios.count()

    def total_entregados(self):
        return self.beneficiarios.filter(retiro__isnull=False).distinct().count()

    def total_pendientes(self):
        return self.beneficiarios.filter(retiro__isnull=True).count()

    def tasa_entrega(self):
        total = self.total_beneficiarios()
        if total == 0:
            return 0
        return round((self.total_entregados() / total) * 100, 1)


class DiaBloquedo(models.Model):
    """Días bloqueados dentro de una campaña"""
    MOTIVOS_CHOICES = [
        ('emergencia', 'Emergencia'),
        ('feriado', 'Feriado'),
        ('mantenimiento', 'Mantenimiento'),
        ('otro', 'Otro'),
    ]

    campana = models.ForeignKey(Campana, on_delete=models.CASCADE, related_name='dias_bloqueados')
    fecha = models.DateField()
    motivo = models.CharField(max_length=20, choices=MOTIVOS_CHOICES, default='emergencia')
    descripcion = models.TextField(blank=True)
    bloqueado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_bloqueo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Día Bloqueado'
        verbose_name_plural = 'Días Bloqueados'
        unique_together = ['campana', 'fecha']
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} - {self.get_motivo_display()}"


class Beneficiario(models.Model):
    """Trabajadores beneficiarios de las cajas"""
    TIPO_CONTRATO_CHOICES = [
        ('indefinido', 'Plazo Indefinido'),
        ('fijo', 'Plazo Fijo'),
    ]

    TIPO_CAJA_CHOICES = [
        ('estandar', 'Estándar'),
        ('especial', 'Especial'),
        ('premium', 'Premium'),
    ]

    campana = models.ForeignKey(Campana, on_delete=models.CASCADE, related_name='beneficiarios')
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, validators=[rut_validator])
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES)
    tipo_caja = models.CharField(max_length=20, choices=TIPO_CAJA_CHOICES, default='estandar')
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE)
    codigo_caja = models.CharField(max_length=15, unique=True, blank=True)

    class Meta:
        verbose_name = 'Beneficiario'
        verbose_name_plural = 'Beneficiarios'
        unique_together = ['campana', 'rut']
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.rut}"

    def tiene_retiro(self):
        return hasattr(self, 'retiro')

    def puede_retirar_hoy(self):
        """Verifica si puede retirar hoy (no está bloqueado el día)"""
        from django.utils import timezone
        hoy = timezone.now().date()
        return not self.campana.dias_bloqueados.filter(fecha=hoy).exists()

    def generar_codigo_caja(self):
        """Genera un código único para la caja basado en campaña, tipo de contrato, planta y correlativo"""
        import re

        # Prefijo según tipo de contrato
        prefijo = 'I' if self.tipo_contrato == 'indefinido' else 'F'

        # Usar fecha de inicio de campaña
        fecha_inicio = self.campana.fecha_inicio
        dia = fecha_inicio.strftime('%d')
        mes = fecha_inicio.strftime('%m')

        # Código corto de la planta
        planta_codigo = self.planta.get_codigo_corto()

        # Obtener el último número correlativo de la campaña para esta planta
        beneficiarios_planta = Beneficiario.objects.filter(
            campana=self.campana,
            planta=self.planta
        ).exclude(codigo_caja='').order_by('id')

        # Encontrar el máximo correlativo
        max_correlativo = 0
        patron = rf'^[IF]-{dia}{mes}{planta_codigo}(\d+)$'

        for beneficiario in beneficiarios_planta:
            match = re.match(patron, beneficiario.codigo_caja)
            if match:
                correlativo = int(match.group(1))
                if correlativo > max_correlativo:
                    max_correlativo = correlativo

        # Nuevo correlativo
        nuevo_correlativo = max_correlativo + 1
        correlativo_str = str(nuevo_correlativo).zfill(2)

        # Generar código
        codigo = f"{prefijo}-{dia}{mes}{planta_codigo}{correlativo_str}"

        return codigo

    def save(self, *args, **kwargs):
        """Generar código automáticamente al guardar"""
        if not self.codigo_caja:
            self.codigo_caja = self.generar_codigo_caja()
        super().save(*args, **kwargs)


class Retiro(models.Model):
    """Registro de retiro de caja"""
    beneficiario = models.OneToOneField(Beneficiario, on_delete=models.CASCADE, related_name='retiro')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    confirmado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)
    retirado_por_tercero = models.BooleanField(default=False)
    nombre_tercero = models.CharField(max_length=200, blank=True)
    rut_tercero = models.CharField(max_length=12, blank=True)
    codigo_caja = models.CharField(max_length=15, unique=True, blank=True)

    class Meta:
        verbose_name = 'Retiro'
        verbose_name_plural = 'Retiros'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.beneficiario.nombre} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """Copiar código del beneficiario al guardar"""
        if not self.codigo_caja and self.beneficiario.codigo_caja:
            self.codigo_caja = self.beneficiario.codigo_caja
        super().save(*args, **kwargs)


class AutorizacionTercero(models.Model):
    """Autorizaciones para que terceros retiren cajas"""
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, related_name='autorizaciones')
    nombre_tercero = models.CharField(max_length=200)
    rut_tercero = models.CharField(max_length=12, validators=[rut_validator])
    fecha_autorizada = models.DateField()
    solo_una_vez = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Autorización Tercero'
        verbose_name_plural = 'Autorizaciones Terceros'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.beneficiario.nombre} autoriza a {self.nombre_tercero}"

    def es_valida_para_fecha(self, fecha):
        """Verifica si la autorización es válida para una fecha específica"""
        if not self.activa:
            return False
        if self.solo_una_vez:
            return self.fecha_autorizada == fecha
        return fecha >= self.fecha_autorizada


class AgendaRetiro(models.Model):
    """Agenda de retiros futuros de trabajadores"""
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, related_name='agendas')
    fecha_agendada = models.DateField()
    confirmado_hoy = models.BooleanField(default=False)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agenda de Retiro'
        verbose_name_plural = 'Agendas de Retiro'
        ordering = ['fecha_agendada']

    def __str__(self):
        return f"{self.beneficiario.nombre} - {self.fecha_agendada}"
