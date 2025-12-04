/**
 * Validación de RUT chileno
 * Formatea automáticamente el RUT agregando el guión si no está presente
 */

// Función para limpiar el RUT (quitar puntos y guión)
function limpiarRut(rut) {
    return rut.replace(/[.-]/g, '');
}

// Función para calcular el dígito verificador
function calcularDigitoVerificador(rutSinDV) {
    let suma = 0;
    let multiplicador = 2;

    // Recorrer el RUT de derecha a izquierda
    for (let i = rutSinDV.length - 1; i >= 0; i--) {
        suma += parseInt(rutSinDV.charAt(i)) * multiplicador;
        multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
    }

    const resto = suma % 11;
    const dv = 11 - resto;

    if (dv === 11) return '0';
    if (dv === 10) return 'K';
    return dv.toString();
}

// Función para detectar si el RUT tiene formato válido o necesita ser completado
function procesarRut(rut) {
    // Limpiar el RUT
    let rutLimpio = limpiarRut(rut.trim());

    // Validar que tenga el largo correcto (mínimo 7 caracteres: números)
    if (rutLimpio.length < 7) {
        return { valido: false, mensaje: 'El RUT es demasiado corto (mínimo 7 dígitos)' };
    }

    // Si el RUT no tiene guión, asumimos que el usuario ingresó solo números
    // y el último carácter es el dígito verificador
    let rutNumero, dvIngresado;

    if (rut.includes('-')) {
        // El usuario ya puso el guión, validar normalmente
        rutNumero = rutLimpio.slice(0, -1);
        dvIngresado = rutLimpio.slice(-1).toUpperCase();
    } else {
        // El usuario NO puso guión, lo agregamos automáticamente
        // Asumimos que el último carácter es el DV
        rutNumero = rutLimpio.slice(0, -1);
        dvIngresado = rutLimpio.slice(-1).toUpperCase();
    }

    // Validar que la parte numérica sea un número válido
    if (!/^\d+$/.test(rutNumero)) {
        return { valido: false, mensaje: 'El RUT debe contener solo números antes del dígito verificador' };
    }

    // Validar que el DV sea válido (número o K)
    if (!/^[0-9kK]$/.test(dvIngresado)) {
        return { valido: false, mensaje: 'El dígito verificador debe ser un número del 0-9 o K' };
    }

    // Calcular el dígito verificador correcto
    const dvCalculado = calcularDigitoVerificador(rutNumero);

    // Comparar
    if (dvIngresado !== dvCalculado) {
        return {
            valido: false,
            mensaje: `RUT inválido. El dígito verificador correcto sería: ${dvCalculado}`,
            rutSugerido: rutNumero + dvCalculado
        };
    }

    return {
        valido: true,
        mensaje: 'RUT válido',
        rutFormateado: formatearRut(rutNumero + dvIngresado)
    };
}

// Función para formatear el RUT (agregar puntos y guión)
function formatearRut(rut) {
    // Limpiar el RUT
    let rutLimpio = limpiarRut(rut);

    // Si está vacío, retornar vacío
    if (rutLimpio.length === 0) return '';

    // Separar el dígito verificador
    const dv = rutLimpio.slice(-1).toUpperCase();
    let numero = rutLimpio.slice(0, -1);

    // Si no hay número, retornar solo lo que se ha escrito
    if (numero.length === 0) return rutLimpio;

    // Formatear con puntos (de derecha a izquierda)
    let numeroFormateado = '';
    let contador = 0;

    for (let i = numero.length - 1; i >= 0; i--) {
        if (contador === 3) {
            numeroFormateado = '.' + numeroFormateado;
            contador = 0;
        }
        numeroFormateado = numero.charAt(i) + numeroFormateado;
        contador++;
    }

    return numeroFormateado + '-' + dv;
}

// Función para formatear RUT mientras se escribe (en tiempo real)
function formatearRutEnTiempoReal(valor) {
    // Limpiar todo excepto números y K
    let limpio = valor.replace(/[^0-9kK]/g, '');

    if (limpio.length === 0) return '';

    // Si tiene más de 1 carácter, agregar el guión antes del último
    if (limpio.length > 1) {
        const cuerpo = limpio.slice(0, -1);
        const dv = limpio.slice(-1);

        // Formatear el cuerpo con puntos
        let cuerpoFormateado = '';
        let contador = 0;

        for (let i = cuerpo.length - 1; i >= 0; i--) {
            if (contador === 3) {
                cuerpoFormateado = '.' + cuerpoFormateado;
                contador = 0;
            }
            cuerpoFormateado = cuerpo.charAt(i) + cuerpoFormateado;
            contador++;
        }

        return cuerpoFormateado + '-' + dv.toUpperCase();
    }

    return limpio;
}

// Función para aplicar validación en tiempo real a un input
function aplicarValidacionRut(inputElement) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'invalid-feedback';
    inputElement.parentNode.insertBefore(feedbackDiv, inputElement.nextSibling);

    // Evento de formateo mientras se escribe
    inputElement.addEventListener('input', function(e) {
        // Guardar posición del cursor antes del formateo
        let cursorPos = e.target.selectionStart;
        const oldValue = e.target.value;
        const oldLength = oldValue.length;

        // Limpiar y formatear
        const valorFormateado = formatearRutEnTiempoReal(oldValue);

        // Si está vacío, limpiar validación
        if (valorFormateado.length === 0) {
            inputElement.classList.remove('is-valid', 'is-invalid');
            feedbackDiv.textContent = '';
            e.target.value = '';
            return;
        }

        // Actualizar el valor
        e.target.value = valorFormateado;

        // Ajustar cursor: simplemente lo colocamos al final
        // Esto evita problemas de saltos del cursor
        const newLength = valorFormateado.length;
        const diff = newLength - oldLength;

        // Si se agregó contenido, mover el cursor
        if (diff > 0) {
            cursorPos += diff;
        }

        // Colocar el cursor al final siempre que se esté escribiendo
        e.target.setSelectionRange(newLength, newLength);

        // Limpiar validación mientras escribe
        inputElement.classList.remove('is-valid', 'is-invalid');
        feedbackDiv.textContent = '';
    });

    // Evento de validación al perder el foco
    inputElement.addEventListener('blur', function(e) {
        const valor = e.target.value.trim();

        if (valor.length === 0) {
            inputElement.classList.remove('is-valid', 'is-invalid');
            feedbackDiv.textContent = '';
            return;
        }

        const resultado = procesarRut(valor);

        if (resultado.valido) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
            feedbackDiv.textContent = '';
            // Formatear el RUT automáticamente (con guión si no lo tenía)
            e.target.value = resultado.rutFormateado;
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
            feedbackDiv.textContent = resultado.mensaje;
        }
    });

    // Validación antes de enviar el formulario
    const form = inputElement.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const valor = inputElement.value.trim();

            if (valor.length === 0) {
                e.preventDefault();
                inputElement.classList.add('is-invalid');
                feedbackDiv.textContent = 'El RUT es obligatorio';
                return false;
            }

            const resultado = procesarRut(valor);

            if (!resultado.valido) {
                e.preventDefault();
                inputElement.classList.remove('is-valid');
                inputElement.classList.add('is-invalid');
                feedbackDiv.textContent = resultado.mensaje;
                inputElement.focus();
                return false;
            }

            // Formatear antes de enviar
            inputElement.value = resultado.rutFormateado;
            return true;
        });
    }
}

// Inicializar automáticamente cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todos los inputs con name="rut" o id="rut"
    const rutInputs = document.querySelectorAll('input[name="rut"], input#rut, input.rut-input');

    rutInputs.forEach(function(input) {
        aplicarValidacionRut(input);
    });
});
