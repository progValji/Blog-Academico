export function validarPassword(valor){
    if (!valor.trim()) return "Ingresa una contraseña"

    const myregex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[^\s]{8,}$/
    if(!myregex.test(valor)) return 'No es una contraeña valida ❌'

    return ''

}