# Sistema de Registro de Cajas - Tres Montes

Sistema Django para el registro y control de entregas de cajas a trabajadores.

## Características

- Validación automática de RUT chileno en tiempo real
- Formateo automático del RUT (agrega puntos y guión)
- Registro de entregas de cajas
- Control de trabajadores con contratos activos
- Reportes de entregas

## Requisitos

- Python 3.8 o superior
- pip

## Instalación

### En Linux/Mac:

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd tresMontes

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### En Windows:

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd tresMontes

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (CMD)
venv\Scripts\activate.bat

# O en PowerShell
venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## Acceso

Abrir el navegador en: `http://localhost:8000`

## Validación de RUT

El sistema incluye validación automática de RUT chileno en el frontend:

- Formateo en tiempo real mientras escribes
- Agrega automáticamente puntos y guión
- Valida el dígito verificador
- Acepta RUT con o sin formato

Ejemplo: Si escribes `123456789`, se formatea automáticamente a `12.345.678-9`

## Tecnologías

- Django 6.0
- Bootstrap 5
- JavaScript vanilla (validación de RUT)
- SQLite

## Estructura del Proyecto

```
tresMontes/
├── registroCajas/        # Aplicación principal
│   ├── models.py         # Modelos (Trabajador, Contrato, Entrega)
│   ├── views.py          # Vistas
│   ├── forms.py          # Formularios
│   └── templates/        # Templates HTML
├── static/
│   └── js/
│       └── rut-validator.js  # Validador de RUT
├── templates/
│   └── base.html         # Template base
└── manage.py
```

## Notas

- La base de datos SQLite se crea automáticamente al ejecutar las migraciones
- El archivo `db.sqlite3` no se sube a GitHub (está en `.gitignore`)
- El entorno virtual (`venv/`) tampoco se sube a GitHub
