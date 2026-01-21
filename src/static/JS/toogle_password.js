const inputs = document.querySelectorAll('.input__formulario')

inputs.forEach(function(container){
    const input = container.querySelector('input')  
    const button = container.querySelector('button')
    
    button.addEventListener('click', function(e){
        e.preventDefault()
        let estado = button.getAttribute('data-visible')

        if(estado == 'false'){
            input.type = 'text'
            button.textContent = '🙈'
            button.setAttribute('data-visible', 'true')
        }else{
            input.type = 'password'
            button.textContent = '👁️'
            button.setAttribute('data-visible', 'false')
        }
    })
})