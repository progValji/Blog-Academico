"""
Paquete de base de datos - Lazy loading
"""

def __getattr__(name):
    if name == 'obtener_conexion':
        from .connection import obtener_conexion
        return obtener_conexion
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['obtener_conexion']
