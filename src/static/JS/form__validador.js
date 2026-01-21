import { validar_email } from "./validadores/email.js";
import { validar_password } from "./validadores/password.js";

export function inicializar_validacion_formulario(form){
    const root = document.documentElement
    const colorErrores = getComputedStyle(root).getPropertyValue('--color-errores').trim()

    const inputs = form.querySelectorAll(".input__formulario input");
    const submitBtn = form.querySelector("button[type='submit']");

    function validar_input(input){
        const contendor = input.closest('.input__formulario')
        const span = contendor.querySelector('span')
        let error = ''
        
        switch(input.type){
            case 'email':
                error = validar_email(input.value)
                break
            case 'password':
                error = validar_password(input.value)
                break
        }

        span.textContent = error
        if(error != ''){
            console.log('errot')
            span.style.opacity = '1'
            input.style.borderColor = colorErrores
        }else{
            console.log('bien')
            span.style.opacity = '0'
            input.style.borderColor = 'inherit'
        }

        return error === ''
    }

    function validar_formulario(){
        let valido = true

        inputs.forEach(input => {
            if(!validar_input(input)){
                valido = false
            }
        })
        submitBtn.disabled = !valido
    }

    inputs.forEach(input => {
        input.addEventListener("blur", () => {
            //validar_input(input);
            validar_formulario();
        });
    });
}