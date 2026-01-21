const input__password = document.querySelectorAll("input[type='password']")

// Obtener las variables de CSS
const root = document.documentElement
const colorErrores = getComputedStyle(root).getPropertyValue('--color-errores').trim()
const colorVerdeMenta = getComputedStyle(root).getPropertyValue('--color-verde__menta').trim()

input__password.forEach(function(input){
    input.addEventListener('blur', function(e){
        const span = input.parentElement.querySelector('span')
        span.style.opacity = '1'
        span.style.fontSize = '.8rem'
        span.style.color = colorErrores
        input.style.borderColor = colorErrores

        if(e.target.value.trim() === ''){
            span.textContent = 'Ingresa una contraseña❌'
            return
        }

        if(e.target.id == 'confirmar_contraseña' || e.target.id == 'nueva_contraseña'){
            const myregex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[^\s]{8,}$/
            const resultado = myregex.test(e.target.value)

            if(!resultado) {
                span.textContent = 'No es una contraseña valida ❌'
                return
            }
        }

        input.style.borderColor = colorVerdeMenta
        span.textContent = 'Contraseña valido ✅'
        span.style.color = colorVerdeMenta
    })
})