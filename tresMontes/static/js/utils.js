/**
 * Formatea un RUT chileno mientras el usuario escribe
 * Formato: XX.XXX.XXX-X (ej: 15.943.503-2)
 * 
 * @param {string} rut - RUT sin formato
 * @returns {string} - RUT formateado
 */
function formatearRUT(rut) {
    // Limpiar: remover puntos y guiones
    let rutLimpio = rut.replace(/[\.\-]/g, '').toUpperCase();
    
    // Mantener solo dígitos y K
    rutLimpio = rutLimpio.replace(/[^\dkK]/g, '');
    
    if (!rutLimpio) return '';
    
    // Limitar a 9 caracteres máximo (8 dígitos + 1 verificador)
    rutLimpio = rutLimpio.substring(0, 9);
    
    // Separar: primeros 8 caracteres son números, el noveno es verificador
    let numeros = rutLimpio.substring(0, 8);
    let verificador = rutLimpio.length > 8 ? rutLimpio.charAt(8) : '';
    
    // Formatear los números con puntos: XX.XXX.XXX
    let rutFormateado = '';
    
    if (numeros.length === 0) {
        rutFormateado = '';
    } else if (numeros.length <= 2) {
        rutFormateado = numeros;
    } else if (numeros.length === 3) {
        rutFormateado = numeros;
    } else if (numeros.length <= 5) {
        // 4-5 dígitos: X.XXX o XX.XXX
        let primera = numeros.substring(0, numeros.length - 3);
        let ultima = numeros.substring(numeros.length - 3);
        rutFormateado = primera + '.' + ultima;
    } else {
        // 6-8 dígitos: XXX.XXX, X.XXX.XXX, XX.XXX.XXX
        let primera = numeros.substring(0, numeros.length - 6);
        let segunda = numeros.substring(numeros.length - 6, numeros.length - 3);
        let tercera = numeros.substring(numeros.length - 3);
        rutFormateado = primera + '.' + segunda + '.' + tercera;
    }
    
    // Añadir guion y verificador si existe
    if (verificador) {
        rutFormateado += '-' + verificador;
    }
    
    return rutFormateado;
}

/**
 * Valida si un RUT chileno es válido (formato y dígito verificador)
 * 
 * @param {string} rut - RUT a validar (con o sin formato)
 * @returns {boolean} - true si el RUT es válido, false en caso contrario
 */
function validarRUT(rut) {
    // Remover puntos y guiones
    let rutLimpio = rut.replace(/[\.\-]/g, '').toUpperCase();
    
    // Verificar que tenga formato: 8 dígitos + 1 verificador (dígito o K)
    if (!/^\d{8}[kK0-9]$/.test(rutLimpio)) {
        return false;
    }
    
    // Separar números y dígito verificador
    let numeros = rutLimpio.slice(0, -1);
    let digito = rutLimpio.slice(-1);
    
    // Calcular dígito verificador
    let suma = 0;
    let multiplicador = 2;
    
    for (let i = numeros.length - 1; i >= 0; i--) {
        suma += parseInt(numeros[i]) * multiplicador;
        multiplicador++;
        if (multiplicador > 7) {
            multiplicador = 2;
        }
    }
    
    let digitoCalculado = 11 - (suma % 11);
    
    if (digitoCalculado === 11) {
        digitoCalculado = 0;
    } else if (digitoCalculado === 10) {
        digitoCalculado = 'K';
    } else {
        digitoCalculado = digitoCalculado.toString();
    }
    
    return digito === digitoCalculado.toString();
}

/**
 * Vincula la función de formateo a un campo de input
 * 
 * @param {string} inputId - ID del elemento input
 */
function vincularFormateadorRUT(inputId) {
    const input = document.getElementById(inputId);
    if (!input) {
        console.warn(`No se encontró elemento con ID: ${inputId}`);
        return;
    }

    // 1. Al salir del campo (Blur): Formateamos visualmente (XX.XXX.XXX-Y)
    input.addEventListener('blur', function() {
        this.value = formatearRUT(this.value);
    });

    // 2. Al entrar al campo (Focus): Limpiamos para facilitar la edición (XXXXXXXXY)
    // Esto evita que el usuario tenga que borrar puntos y guiones manualmente
    input.addEventListener('focus', function() {
        this.value = limpiarRUT(this.value);
    });
}

// Función auxiliar para limpiar (déjala disponible en tu scope)
function limpiarRUT(rut) {
    return rut.replace(/[^0-9kK]/g, ''); // Deja solo números y K
}

// Exportar funciones (para uso en módulos si es necesario)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatearRUT, validarRUT, vincularFormateadorRUT };
}
