"""
Utilidades de seguridad
"""
import secrets
from ..config import RETRASO_BASE


def generar_token():
    """
    Genera un token seguro para recuperación de contraseña
    
    Returns:
        str: Token criptográfico URL-safe de 32 bytes
    """
    return secrets.token_urlsafe(32)


def calcular_retraso_exponencial(intenos_fallidos):
    """
    Calcula el tiempo de retraso exponencial basado en intentos fallidos
    
    Args:
        intenos_fallidos (int): Número de intentos fallidos
        
    Returns:
        int: Segundos de retraso (2^(intenos-1))
    """
    if intenos_fallidos == 0:
        return 0
    return RETRASO_BASE ** (intenos_fallidos - 1)
