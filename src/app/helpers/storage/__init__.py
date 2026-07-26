"""
Paquete de almacenamiento - Lazy loading
"""

def __getattr__(name):
    if name == 'allowed_file':
        from .files import allowed_file
        return allowed_file
    elif name == 'extraer_archivo':
        from .files import extraer_archivo
        return extraer_archivo
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['allowed_file', 'extraer_archivo']
