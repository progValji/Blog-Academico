export function validar_password(valor){
    if (!valor.trim()) return "La contraseña es obligatoria"

    const myregex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[^\s]{8,}$/
    if(!myregex.test(valor)) return 'No es una contraeña valida ❌'

    return ''

}