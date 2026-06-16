export function validarPassword(valor) {
    if (!valor.trim()) return "Ingresa una contraseña";

    if (valor.length < 8)
        return "Debe tener al menos 8 caracteres";

    if (!/[A-Z]/.test(valor))
        return "Debe contener al menos una letra mayúscula";

    if (!/[a-z]/.test(valor))
        return "Debe contener al menos una letra minúscula";

    if (!/\d/.test(valor))
        return "Debe contener al menos un número";

    if (/\s/.test(valor))
        return "No debe contener espacios";

    return "";
}