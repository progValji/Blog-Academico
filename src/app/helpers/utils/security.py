"""
Utilidades de seguridad
"""
import secrets
from ..config import RETRASO_BASE
import re


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

def validar_email(correo):
    if not correo.strip():
        return "Ingresa un correo"

    regex = r"^[-\w.%+]{1,64}@(?:[A-Za-z0-9-]{1,63}\.){1,125}[A-Za-z]{2,63}$"

    if not re.match(regex, correo):
        return False

    return True

import re

def validar_password(password):
    if not password.strip():
        return "Ingresa una contraseña"

    if len(password) < 8:
        return "Debe tener al menos 8 caracteres"

    if not re.search(r"[A-Z]", password):
        return "Debe contener al menos una letra mayúscula"

    if not re.search(r"[a-z]", password):
        return "Debe contener al menos una letra minúscula"

    if not re.search(r"\d", password):
        return "Debe contener al menos un número"

    if re.search(r"\s", password):
        return "No debe contener espacios"

    return ""
