import { validarEmail } from "./validadores/email.js";
import { validarPassword } from "./validadores/password.js";
import { validarNombre } from "./validadores/nombre.js";

export function inicializarValidacionFormulario(form){
    const root = document.documentElement
    const colorErrores = getComputedStyle(root).getPropertyValue('--color-errores').trim()

    const inputs = form.querySelectorAll(".input__formulario input");
    const submitBtn = form.querySelector("button[type='submit']");
    const touched = new Set()

    function validarInput(input){
        const contendor = input.closest('.input__formulario')
        const span = contendor.querySelector('span')
        let error = ''
        
        switch(input.type){
            case 'email':
                error = validarEmail(input.value)
                break
            case 'password':
                error = validarPassword(input.value)
                break
            default:
                if(input.id == "contraseña")
                    error = validarPassword(input.value)
                if(input.id == "nombre")
                    error = validarNombre(input.value)
        }

        if(touched.has(input)){
            span.textContent = error
            if(error != ''){
                span.style.opacity = '1'
                input.style.borderColor = colorErrores
            }else{
                span.style.opacity = '0'
                input.style.borderColor = 'inherit'
            }
        }

        return error === ''
    }

    function validarFormulario(){
        let valido = true

        inputs.forEach(input => {
            if(!validarInput(input)){
                valido = false
            }
        })
        submitBtn.disabled = !valido
    }

    inputs.forEach(input => {
        input.addEventListener("blur", () => {
            touched.add(input)
            validarInput(input);
            validarFormulario();
        });
    });
}