from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trabajador, Contrato, Entrega
from .forms import CSVUploadForm


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
    from django.utils import timezone
    from django.db.models import Q
    
    now = timezone.now()
    today = now.date()
    
    # Entregas realizadas hoy
    entregas_hoy = Entrega.objects.filter(
        fecha_entrega__date=today
    ).count()
    
    # Trabajadores con contrato activo que NO han retirado este mes
    trabajadores_con_contrato = Trabajador.objects.filter(
        contratos__activo=True
    ).distinct()
    
    trabajadores_con_entrega_este_mes = Trabajador.objects.filter(
        entregas__fecha_entrega__month=now.month,
        entregas__fecha_entrega__year=now.year
    ).distinct()
    
    pendientes = trabajadores_con_contrato.exclude(
        id__in=trabajadores_con_entrega_este_mes.values_list('id', flat=True)
    ).count()
    
    # Últimas 10 entregas
    entregas_recientes_objs = Entrega.objects.select_related('trabajador').order_by('-fecha_entrega')[:10]
    entregas_recientes = [
        {
            'nombre': f"{e.trabajador.nombre} {e.trabajador.apellido}",
            'estado': 'entregado',
            'fecha': e.fecha_entrega
        }
        for e in entregas_recientes_objs
    ]
    
    context = {
        'entregas_hoy': entregas_hoy,
        'pendientes': pendientes,
        'entregas_recientes': entregas_recientes
    }
    return render(request, 'registroCajas/panel_principal.html', context)

@login_required
def buscar_trabajador(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')
        try:
            trabajador = Trabajador.objects.get(rut=rut)
            # Buscar contrato activo
            contrato = trabajador.contratos.filter(activo=True).first()
            
            if not contrato:
                messages.error(request, 'El trabajador no tiene un contrato activo.')
                return redirect('buscar_trabajador')

            # Verificar si ya retiró caja en el periodo actual (ej. este mes/año)
            # Para simplificar PMV, verificamos si tiene entrega hoy o en el rango del contrato
            # Asumimos una entrega por contrato/periodo. 
            # Ajustar lógica según requerimiento exacto. Por ahora: 1 entrega por mes.
            from django.utils import timezone
            now = timezone.now()
            entrega_existente = Entrega.objects.filter(
                trabajador=trabajador, 
                fecha_entrega__month=now.month, 
                fecha_entrega__year=now.year
            ).exists()

            context = {
                'trabajador': trabajador,
                'contrato': contrato,
                'entrega_existente': entrega_existente
            }
            return render(request, 'registroCajas/confirmacion.html', context)

        except Trabajador.DoesNotExist:
            messages.error(request, 'Trabajador no encontrado.')
            return redirect('buscar_trabajador')

    return render(request, 'registroCajas/verificacion.html')

@login_required
def registrar_entrega(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')
        try:
            trabajador = Trabajador.objects.get(rut=rut)
            # Re-validar condiciones para seguridad
            contrato = trabajador.contratos.filter(activo=True).first()
            if not contrato:
                messages.error(request, 'Error: Contrato no activo.')
                return redirect('panel_principal')

            from django.utils import timezone
            now = timezone.now()
            if Entrega.objects.filter(trabajador=trabajador, fecha_entrega__month=now.month, fecha_entrega__year=now.year).exists():
                 messages.error(request, 'Error: Ya se entregó caja este mes.')
                 return redirect('panel_principal')

            # Registrar entrega
            Entrega.objects.create(
                trabajador=trabajador,
                guardia=request.user
            )
            messages.success(request, f'Entrega registrada para {trabajador.nombre} {trabajador.apellido}')
            return redirect('panel_principal')

        except Trabajador.DoesNotExist:
             messages.error(request, 'Error: Trabajador no encontrado.')
             return redirect('panel_principal')
    
    return redirect('panel_principal')

@login_required
def importar_trabajadores(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'El archivo no es un CSV')
                return redirect('importar_trabajadores')

            import csv
            import io

            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string) # Skip header

            for column in csv.reader(io_string, delimiter=',', quotechar='"'):
                # Expected format: RUT, NOMBRES, APELLIDOS, CARGO, TIPO DE CONTRATO, PERIODO, SEDE, ESTADO
                try:
                    rut = column[0]
                    nombre = column[1]
                    apellido = column[2]
                    cargo = column[3]
                    tipo_contrato = column[4]
                    periodo = column[5]
                    sede = column[6]
                    estado = column[7]

                    obj, created = Trabajador.objects.update_or_create(
                        rut=rut,
                        defaults={
                            'nombre': nombre,
                            'apellido': apellido,
                            'cargo': cargo,
                            'tipo_contrato': tipo_contrato,
                            'periodo': periodo,
                            'sede': sede,
                            'estado': estado
                        }
                    )
                    
                    # Create active contract if worker doesn't have one
                    if not obj.contratos.filter(activo=True).exists():
                        from django.utils import timezone
                        Contrato.objects.create(
                            trabajador=obj,
                            tipo_caja='estandar',
                            fecha_inicio=timezone.now().date(),
                            activo=True
                        )
                except IndexError:
                    continue # Skip malformed lines

            messages.success(request, 'Trabajadores importados correctamente')
            return redirect('panel_principal')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = CSVUploadForm()

    return render(request, 'registroCajas/importar_trabajadores.html', {'form': form})

@login_required
def reportes(request):
    from django.utils import timezone
    
    now = timezone.now()
    
    # Get all workers with active contracts
    trabajadores = Trabajador.objects.filter(contratos__activo=True).distinct()
    
    # Build list with status
    trabajadores_data = []
    for trabajador in trabajadores:
        # Check if has delivery this month
        tiene_entrega = Entrega.objects.filter(
            trabajador=trabajador,
            fecha_entrega__month=now.month,
            fecha_entrega__year=now.year
        ).exists()
        
        trabajadores_data.append({
            'trabajador': trabajador,
            'estado': 'entregado' if tiene_entrega else 'pendiente'
        })
    
    context = {
        'trabajadores_data': trabajadores_data
    }
    return render(request, 'registroCajas/reportes.html', context)