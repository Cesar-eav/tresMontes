/**
 * ============================================================================
 * RUT VALIDACIÓN - SOLO PARA CREAR/EDITAR USUARIO
 * ============================================================================
 * Formatea Y valida con algoritmo Módulo 11
 * Usado en: crear_usuario, editar_usuario
 */

/**
 * Limpia un RUT removiendo puntos y guiones
 */
function limpiarRUTUsuario(rut) {
    if (!rut) return '';
    return rut.replace(/[^0-9kK]/g, '').toUpperCase();
}

/**
 * Formatea un RUT mientras el usuario escribe
 * Formato: XX.XXX.XXX-X
 */
function formatearRUTUsuario(rut) {
    let rutLimpio = limpiarRUTUsuario(rut);

    if (!rutLimpio) return '';

    // Limitar a 9 caracteres
    rutLimpio = rutLimpio.substring(0, 9);

    // Separar números y verificador (último carácter)
    let numeros = rutLimpio.slice(0, -1);
    let verificador = rutLimpio.slice(-1);

    // Si solo hay 1 carácter, retornarlo sin formato
    if (rutLimpio.length === 1) {
        return rutLimpio;
    }

    // Formatear números con puntos
    let rutFormateado = '';

    if (numeros.length <= 2) {
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

    // Añadir guion y verificador
    rutFormateado += '-' + verificador;

    return rutFormateado;
}

/**
 * Valida un RUT chileno con algoritmo Módulo 11
 * Retorna true si es válido, false si es inválido
 */
function validarRUTUsuario(rut) {
    if (typeof rut === 'number') rut = rut.toString();
    if (!rut || typeof rut !== 'string') return false;

    let rutLimpio = limpiarRUTUsuario(rut);

    // Verificar formato: 1-8 dígitos + 1 verificador
    if (!/^\d{1,8}[kK0-9]$/.test(rutLimpio)) {
        return false;
    }

    // Separar números y verificador
    let numeros = rutLimpio.slice(0, -1);
    let digitoIngresado = rutLimpio.slice(-1);

    // Calcular dígito verificador con Módulo 11
    let suma = 0;
    let multiplicador = 2;

    for (let i = numeros.length - 1; i >= 0; i--) {
        suma += parseInt(numeros[i]) * multiplicador;
        multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
    }

    let resto = suma % 11;
    let digitoCalculado = 11 - resto;

    // Convertir a formato correcto
    let digitoEsperado;
    if (digitoCalculado === 11) {
        digitoEsperado = '0';
    } else if (digitoCalculado === 10) {
        digitoEsperado = 'K';
    } else {
        digitoEsperado = digitoCalculado.toString();
    }

    return digitoIngresado === digitoEsperado;
}

/**
 * Vincula formateador Y validador a un input de usuario
 * Formatea en tiempo real y valida al salir del campo
 */
function vincularFormateadorUsuarioRUT(inputId) {
    const input = document.getElementById(inputId);
    if (!input) {
        console.warn(`[RUT-USUARIO] No se encontró elemento: ${inputId}`);
        return;
    }

    // Configuración visual
    input.setAttribute('maxlength', '12');
    input.setAttribute('placeholder', 'XX.XXX.XXX-X');

    // Formateo en tiempo real
    input.addEventListener('input', function(e) {
        const isBackspace = (e.inputType === 'deleteContentBackward');
        const valorRaw = limpiarRUTUsuario(this.value);

        if (valorRaw.length === 0) {
            this.value = '';
            // Remover clases de validación
            this.classList.remove('is-valid', 'is-invalid');
            return;
        }

        // Guardar posición del cursor respecto a dígitos
        const selectionStart = this.selectionStart;
        const valueBefore = this.value;

        let digitsBeforeCursor = 0;
        for (let i = 0; i < selectionStart; i++) {
            if (/[0-9kK]/.test(valueBefore[i])) digitsBeforeCursor++;
        }

        // Aplicar formato
        const newValue = formatearRUTUsuario(valorRaw);

        if (newValue === valueBefore) return;

        this.value = newValue;

        // Restaurar cursor
        let newCursorPos = 0;
        let digitsSeen = 0;

        for (let i = 0; i < newValue.length; i++) {
            if (/[0-9kK]/.test(newValue[i])) {
                digitsSeen++;
            }
            newCursorPos++;
            if (digitsSeen === digitsBeforeCursor) break;
        }

        // Ajuste para backspace
        if (isBackspace && newCursorPos > 0 && !/[0-9kK]/.test(newValue[newCursorPos-1])) {
            newCursorPos--;
        }

        this.setSelectionRange(newCursorPos, newCursorPos);
    });

    // Validación al salir del campo
    input.addEventListener('blur', function() {
        const rut = this.value.trim();

        if (!rut) {
            this.classList.remove('is-valid', 'is-invalid');
            return;
        }

        const esValido = validarRUTUsuario(rut);

        if (esValido) {
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
        } else {
            this.classList.remove('is-valid');
            this.classList.add('is-invalid');
        }
    });

    console.log(`[RUT-USUARIO] Vinculado: ${inputId}`);
}
