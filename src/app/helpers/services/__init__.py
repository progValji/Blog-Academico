"""
Paquete de servicios de negocio - Lazy loading
"""

def __getattr__(name):
    if name == 'enviar_correo':
        from .email_service import enviar_correo
        return enviar_correo
    elif name == 'salvar_post':
        from .post_service import salvar_post
        return salvar_post
    elif name == 'agrupar_filas_posts':
        from .post_service import agrupar_filas_posts
        return agrupar_filas_posts
    elif name == 'salvar_comentario':
        from .comment_service import salvar_comentario
        return salvar_comentario
    elif name == 'upload_files_to_idrive':
        from .idrive2_service import upload_files_to_idrive
        return upload_files_to_idrive
    elif name == 'eliminar_archivos_post_idrive':
        from .idrive2_service import eliminar_archivos_post_idrive
        return eliminar_archivos_post_idrive
    
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'enviar_correo',
    'salvar_post',
    'agrupar_filas_posts',
    'salvar_comentario',
    'upload_files_to_idrive',
    'eliminar_archivos_post_idrive'
]

