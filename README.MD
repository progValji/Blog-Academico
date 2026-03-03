# Cosas a mejorar
+ Cuando se tenga dominio propio: configurar un email profesional y ahi 
usar ese email 
~~~py
    app.config['MAIL_USERNAME'] = 'contacto@blogacademico.com'
    app.config['MAIL_DEFAULT_SENDER'] = ('Blog Académico', 'contacto@blogacademico.com')
~~~

+ Animacion formulario
El plan original era que en desktop first hubiera una animacion al momento de cambiar entre el formulario
de inicio y registro

+ Comentarios
Permitir que usuarios no registrados puedan comentar, esos comenatios iran a la parte de administrar 
comentarios, en el cual los usuaios registrados podran admitirlos, pedirles cambios o rechazarlos

# Consideraciones
+Si tu app crece mucho (miles de posts):
    COUNT(*) puede volverse costoso.
En ese caso se usa:
    Paginación basada en cursor (cursor pagination)
    O solo botón "Cargar más"

# Paleta de Colores
Opción 2: Moderna y Equilibrada
Azul petróleo (#2B6E8C) - Principal
Negro suave (#333333) - Textos
Blanco (#FFFFFF) - Fondo
Verde menta (#4ECDC4) - Acentos
Gris neutral (#E8E8E8) - Elementos secundarios