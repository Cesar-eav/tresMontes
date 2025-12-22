# Formato de archivos CSV para Nóminas

El sistema ahora acepta **DOS formatos** de archivos CSV para cargar nóminas de beneficiarios.

---

## Formato Simplificado (Recomendado) ⭐

### Estructura: 5 columnas

```csv
RUT,NOMBRE,TIPO_CONTRATO,TIPO_CAJA,PLANTA_ID
```

### Descripción de columnas:

1. **RUT** - RUT del beneficiario en formato chileno (12.345.678-9)
2. **NOMBRE** - Nombre completo del beneficiario
3. **TIPO_CONTRATO** - Tipo de contrato del trabajador
   - `Indefinido`, `Plazo Indefinido` o `Planta` → Se guarda como "planta"
   - `Plazo Fijo`, `Fijo` o `Contratista` → Se guarda como "contratista"
4. **TIPO_CAJA** - Tipo de caja a entregar
   - `estandar` - Caja estándar (por defecto)
   - `especial` - Caja especial
   - `premium` - Caja premium
5. **PLANTA_ID** - ID numérico de la planta
   - `1` = Casa Blanca
   - `2` = Valparaíso Planta BIF
   - `3` = Valparaíso Planta BIC

### Ejemplo:

```csv
RUT,NOMBRE,TIPO_CONTRATO,TIPO_CAJA,PLANTA_ID
16.543.210-9,Roberto Carlos Gómez Silva,Indefinido,estandar,1
17.234.567-8,Claudia Patricia Torres Muñoz,Plazo Fijo,estandar,2
18.876.543-2,Fernando Andrés Díaz Rojas,Indefinido,especial,1
15.987.654-3,Miguel Ángel Ruiz Pérez,Plazo Fijo,premium,3
```

---

## Formato Extendido (Legacy)

### Estructura: 9 columnas

```csv
RUT,EMPLEADO,NOMBRES,APELLIDOS,CARGO,TIPO DE CONTRATO,PERIODO,SEDE,ESTADO
```

### Descripción de columnas:

1. **RUT** - RUT del beneficiario
2. **EMPLEADO** - Primer nombre
3. **NOMBRES** - Segundo nombre o nombres adicionales
4. **APELLIDOS** - Apellidos completos
5. **CARGO** - Cargo del trabajador (se ignora en el procesamiento)
6. **TIPO DE CONTRATO** - Tipo de contrato (igual que formato simplificado)
7. **PERIODO** - Año o período (se ignora en el procesamiento)
8. **SEDE** - Planta/Sede donde trabaja (se mapea automáticamente)
9. **ESTADO** - Estado (se ignora en el procesamiento)

**Nota:**
- Las columnas EMPLEADO, NOMBRES y APELLIDOS se concatenan para formar el nombre completo.
- TIPO_CAJA se asigna como 'estandar' por defecto en este formato.

### Ejemplo:

```csv
RUT,EMPLEADO,NOMBRES,APELLIDOS,CARGO,TIPO DE CONTRATO,PERIODO,SEDE,ESTADO
16.543.210-9,Roberto Carlos,Gómez,Silva,Operario,Indefinido,2024,Casa Blanca,PENDIENTE
17.234.567-8,Claudia Patricia,Torres,Muñoz,Supervisora,Plazo Fijo,2024,Valparaíso BIF,PENDIENTE
```

---

## Mapeo de Plantas/Sedes (Solo formato extendido)

En el formato extendido, el sistema mapea automáticamente los nombres de sede:

| Valores aceptados en CSV | Planta en sistema | ID |
|---------------------------|-------------------|----|
| Casa Blanca, Santiago, Casablanca | Casa Blanca | 1 |
| Valparaíso BIF, Valparaiso BIF | Valparaíso Planta BIF | 2 |
| Valparaíso BIC, Valparaiso BIC | Valparaíso Planta BIC | 3 |

**En formato simplificado:** Usa directamente el ID numérico (1, 2, 3).

---

## Campos de la Base de Datos

La tabla `registroCajas_beneficiario` tiene estos campos:

| Campo | Tipo | Descripción | Origen en CSV |
|-------|------|-------------|---------------|
| **id** | int | ID único del beneficiario | Auto-generado |
| **nombre** | varchar | Nombre completo | Columna NOMBRE (simplificado) o EMPLEADO+NOMBRES+APELLIDOS (extendido) |
| **rut** | varchar | RUT del beneficiario | Columna RUT |
| **tipo_contrato** | varchar | Tipo de contrato (planta/contratista) | Columna TIPO_CONTRATO mapeada |
| **tipo_caja** | varchar | Tipo de caja (estandar/especial/premium) | Columna TIPO_CAJA o 'estandar' por defecto |
| **campana_id** | int | ID de la campaña | Asignado al crear la carga |
| **planta_id** | int | ID de la planta | Columna PLANTA_ID o mapeado desde SEDE |
| **codigo_caja** | varchar | Código único de la caja | Auto-generado (formato: I-DDMMPLANTAXX o F-DDMMPLANTAXX) |

---

## Archivos de Ejemplo

- **Formato simplificado:** `nomina_ejemplo_simplificado.csv` o `nomina_ejemplo_correcto.csv`
- **Formato extendido:** `nomina_ejemplo_correcto_real.csv`

---

## Validaciones

El sistema valida:
- ✅ Archivo no vacío
- ✅ Al menos 4 columnas en el encabezado
- ✅ RUT no vacío
- ✅ Nombre no vacío
- ✅ Formato de RUT chileno válido (XX.XXX.XXX-X)
- ✅ TIPO_CAJA válido (estandar, especial, premium)
- ✅ PLANTA_ID válido (1, 2, 3) o nombre mapeado

---

## Notas Importantes

1. **Encoding:** El archivo debe estar en UTF-8 (con o sin BOM)
2. **Delimitador:** El sistema detecta automáticamente si usa comas (`,`) o tabuladores (`\t`)
3. **Encabezado obligatorio:** La primera fila debe contener los nombres de las columnas
4. **Filas vacías:** Se ignoran automáticamente
5. **RUTs duplicados:** Si un RUT ya existe en la misma campaña, se salta (no se duplica)
6. **Campos opcionales en formato simplificado:**
   - Si TIPO_CAJA está vacío o es inválido, se usa 'estandar'
   - Si PLANTA_ID está vacío, se usa la planta seleccionada al crear la campaña

---

## Recomendación

**Usa el formato simplificado de 5 columnas** ya que:
- ✅ Es más directo y fácil de crear
- ✅ Mapea 1:1 con los campos de la base de datos
- ✅ Permite especificar TIPO_CAJA
- ✅ No tiene columnas que se ignoran
- ✅ Menos propenso a errores de formato
