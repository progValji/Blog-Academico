const input = document.querySelector('#correo')
const contenedor_input = document.querySelector('.input__formulario')

// Obtener las variables de CSS
const root = document.documentElement
const colorErrores = getComputedStyle(root).getPropertyValue('--color-errores').trim()
const colorVerdeMenta = getComputedStyle(root).getPropertyValue('--color-verde__menta').trim()

input.addEventListener('blur', function(e){
    const span = contenedor_input.querySelector('span')
    span.style.opacity = '1'
    span.style.fontSize = '.8rem'
    span.style.color = colorErrores
    input.style.borderColor = colorErrores

    if(e.target.value.trim() === ''){
        span.textContent = 'El input esta vacio ❌'
        return
    }
    else if(e.target.id == 'correo'){
        const regex = /^[-\w.%+]{1,64}@(?:[A-Z0-9-]{1,63}\.){1,125}[A-Z]{2,63}$/i
        const resultado = regex.test(e.target.value)

        if(!resultado) {
            span.textContent = 'No es un correo valido ❌'
            return
        }
    }
    input.style.borderColor = colorVerdeMenta
    span.textContent = 'Correo valido ✅'
    span.style.color = colorVerdeMenta
})