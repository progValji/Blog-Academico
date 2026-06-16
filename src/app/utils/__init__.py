"""
Paquete de utilidades - Lazy loading para evitar cargar dependencias innecesarias
"""

def __getattr__(name):
    if name == 'generar_token':
        from .security import generar_token
        return generar_token
    elif name == 'calcular_retraso_exponencial':
        from .security import calcular_retraso_exponencial
        return calcular_retraso_exponencial
    elif name == 'limpiar_contenido':
        from .text import limpiar_contenido
        return limpiar_contenido
    elif name == 'generar_paginas':
        from .pagination import generar_paginas
        return generar_paginas
    elif name == 'obtener_datos_paginados':
        from .pagination import obtener_datos_paginados
        return obtener_datos_paginados
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'generar_token',
    'calcular_retraso_exponencial',
    'limpiar_contenido',
    'generar_paginas',
    'obtener_datos_paginados'
]

