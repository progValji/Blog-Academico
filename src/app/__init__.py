"""
Paquete de aplicación
Contiene toda la lógica modularizada de la aplicación Flask

Importaciones:
  - from src.app import obtener_conexion  (requiere pymysql)
  - from src.app import salvar_post       (requiere flask, pymysql)
  - from src.app.utils import generar_token  (sin dependencias externas)
  - from src.app.config import POSTS_POR_PAGINA
"""

# Importaciones opcionales - solo se cargan si se usan explícitamente
def __getattr__(name):
    """Lazy loading de importaciones para evitar cargar dependencias innecesarias"""
    
    if name == 'obtener_conexion':
        from .database import obtener_conexion
        return obtener_conexion
    elif name == 'enviar_correo':
        from .services import enviar_correo
        return enviar_correo
    elif name == 'salvar_post':
        from .services import salvar_post
        return salvar_post
    elif name == 'agrupar_filas_posts':
        from .services import agrupar_filas_posts
        return agrupar_filas_posts
    elif name == 'salvar_comentario':
        from .services import salvar_comentario
        return salvar_comentario
    elif name == 'allowed_file':
        from .storage import allowed_file
        return allowed_file
    elif name == 'borrar_archivos':
        from .storage import borrar_archivos
        return borrar_archivos
    elif name == 'extraer_archivo':
        from .storage import extraer_archivo
        return extraer_archivo
    elif name == 'generar_token':
        from .utils import generar_token
        return generar_token
    elif name == 'calcular_retraso_exponencial':
        from .utils import calcular_retraso_exponencial
        return calcular_retraso_exponencial
    elif name == 'limpiar_contenido':
        from .utils import limpiar_contenido
        return limpiar_contenido
    elif name == 'generar_paginas':
        from .utils import generar_paginas
        return generar_paginas
    elif name == 'obtener_datos_paginados':
        from .utils import obtener_datos_paginados
        return obtener_datos_paginados
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Importaciones directas de constantes (sin dependencias)
from .config import (
    MAX_INTENTOS,
    TIEMPO_BLOQUEADO,
    TIEMPO_TOKEN,
    RETRASO_BASE,
    POSTS_POR_PAGINA,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
)

__all__ = [
    # Database
    'obtener_conexion',
    # Services
    'enviar_correo',
    'salvar_post',
    'agrupar_filas_posts',
    'salvar_comentario',
    # Storage
    'allowed_file',
    'borrar_archivos',
    'extraer_archivo',
    # Utils
    'generar_token',
    'calcular_retraso_exponencial',
    'limpiar_contenido',
    'generar_paginas',
    'obtener_datos_paginados',
    # Config
    'MAX_INTENTOS',
    'TIEMPO_BLOQUEADO',
    'TIEMPO_TOKEN',
    'RETRASO_BASE',
    'POSTS_POR_PAGINA',
    'UPLOAD_FOLDER',
    'ALLOWED_EXTENSIONS',
]

