from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Trabajador(models.Model):
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    nombre = models.CharField(max_length=100, verbose_name="Nombres")
    apellido = models.CharField(max_length=100, verbose_name="Apellidos")
    created_at = models.DateTimeField(auto_now_add=True)
    cargo = models.CharField(max_length=100, verbose_name="Cargo", null=True, blank=True)
    sede = models.CharField(max_length=100, verbose_name="Sede", null=True, blank=True)
    tipo_contrato = models.CharField(max_length=100, verbose_name="Tipo de Contrato", null=True, blank=True)
    periodo = models.CharField(max_length=100, verbose_name="Periodo", null=True, blank=True)
    estado = models.CharField(max_length=50, verbose_name="Estado", null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

class Contrato(models.Model):
    TIPO_CAJA_CHOICES = [
        ('estandar', 'Caja Estándar'),
        ('premium', 'Caja Premium'),
        ('dieciochera', 'Caja Dieciochera'),
        ('navidad', 'Caja Navidad'),
    ]

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='contratos')
    tipo_caja = models.CharField(max_length=20, choices=TIPO_CAJA_CHOICES, default='estandar')
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Término")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Contrato {self.get_tipo_caja_display()} - {self.trabajador}"

class Entrega(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='entregas')
    guardia = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='entregas_realizadas')
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Entrega a {self.trabajador} - {self.fecha_entrega.strftime('%d/%m/%Y %H:%M')}"
