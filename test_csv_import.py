import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tresMontes.settings')
django.setup()

from registroCajas.views import importar_trabajadores
from registroCajas.models import Trabajador

def test_import():
    csv_content = b"""RUT,NOMBRES,APELLIDOS,CARGO,TIPO DE CONTRATO,PERIODO,SEDE,ESTADO
12345678-9,Juan,Perez,Guardia,Indefinido,2023,Central,PENDIENTE
98765432-1,Maria,Gonzalez,Supervisor,Plazo Fijo,2023,Norte,RETIRADO
"""
    csv_file = SimpleUploadedFile("trabajadores.csv", csv_content, content_type="text/csv")
    
    factory = RequestFactory()
    request = factory.post('/importar/', {'csv_file': csv_file})
    
    # Simulate logged in user if needed, but the view uses @login_required. 
    # For unit test we can bypass or mock, but here we are running as script.
    # Let's use Client instead for full integration test.
    
    from django.test import Client
    from django.contrib.auth.models import User
    
    if not User.objects.filter(username='testadmin').exists():
        User.objects.create_superuser('testadmin', 'admin@example.com', 'password')
        
    c = Client()
    c.login(username='testadmin', password='password')
    
    response = c.post('/importar/', {'csv_file': csv_file})
    
    print(f"Response status: {response.status_code}")
    if response.status_code != 302:
        print(f"Response content: {response.content.decode()[:500]}")
    
    t1 = Trabajador.objects.filter(rut='12345678-9').first()
    t2 = Trabajador.objects.filter(rut='98765432-1').first()
    
    if t1 and t1.cargo == 'Guardia':
        print("Worker 1 imported successfully")
    else:
        print("Worker 1 failed")
        
    if t2 and t2.estado == 'RETIRADO':
        print("Worker 2 imported successfully")
    else:
        print("Worker 2 failed")

if __name__ == "__main__":
    test_import()
