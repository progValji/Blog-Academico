export function validarNombre(valor) {

    if (!valor.trim()) 
        return "El nombre es obligatorio";

    if (valor.trim().length < 3) 
        return "El nombre es muy corto";

    // Solo letras (incluye acentos) y espacios
    if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(valor))
        return "El nombre solo puede contener letras";

    return "";
}