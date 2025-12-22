/**
 * ============================================================================
 * RUT FORMATEO - ESPECIAL PARA BÚSQUEDA EN BASE DE DATOS VARCHAR
 * ============================================================================
 * Estrategia: "Formateo Optimista de Izquierda a Derecha"
 * * Problema: La BD tiene "14.567.890-1".
 * - Si formateamos normal (derecha a izquierda), al escribir "1456" genera "1.456".
 * - "1.456" NO calza con el string "14.56..." de la BD.
 * * Solución: Asumimos formato XX.XXX.XXX y agregamos puntos fijos.
 */

function limpiarRUTFiltro(rut) {
    if (!rut) return '';
    return rut.replace(/[^0-9kK]/g, '').toUpperCase();
}

/**
 * Formatea estrictamente para coincidir con strings de BD tipo "12.345.678-9"
 * Asume RUTs mayores a 10 millones (los más comunes en laboral)
 */
function formatearRUTFiltro(rut) {
    let rutLimpio = limpiarRUTFiltro(rut);
    if (!rutLimpio) return '';

    // Si tiene 1 dígito, devolvemos tal cual (Ej: "1")
    if (rutLimpio.length <= 1) return rutLimpio;

    let resultado = '';

    // 1. Primeros 2 dígitos + Punto (Ej: "14" -> "14.")
    // Esto asegura match inmediato con "14.5..." de la BD
    resultado = rutLimpio.substring(0, 2);

    if (rutLimpio.length > 2) {
        resultado += '.' + rutLimpio.substring(2, 5);
    }

    if (rutLimpio.length > 5) {
        resultado += '.' + rutLimpio.substring(5, 8);
    }

    if (rutLimpio.length > 8) {
        resultado += '-' + rutLimpio.substring(8, 9);
    }

    return resultado;
}

/**
 * Vincula el formateador optimista al campo de búsqueda
 */
function vincularFormateadorFiltroRUT(inputId) {
    const input = document.getElementById(inputId);
    if (!input) {
        console.warn(`[RUT-FILTRO] No se encontró elemento: ${inputId}`);
        return;
    }

    input.addEventListener('input', function(e) {
        // Detectar si está borrando (Backspace) para no forzar el formato y bloquear el borrado
        const isBackspace = (e.inputType === 'deleteContentBackward');
        
        if (isBackspace) {
            // Si borra, dejamos que borre natural, solo limpiamos caracteres inválidos
            // Esto evita que el punto se "regenere" infinitamente al intentar borrarlo
            return; 
        }

        const valorActual = this.value;
        const valorFormateado = formatearRUTFiltro(valorActual);
        
        if (valorActual !== valorFormateado) {
            this.value = valorFormateado;
        }
    });

    console.log(`[RUT-FILTRO] Formateador VARCHAR DB vinculado: ${inputId}`);
}

// EXPORTACIÓN (Si usas módulos, si no, ignora esto)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { vincularFormateadorFiltroRUT };
}