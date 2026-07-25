"""
Servicio de envío de correos electrónicos usando la API de Brevo (HTTP/HTTPS)
"""
import os
import requests
from flask import url_for
from dotenv import load_dotenv

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
load_dotenv()

def enviar_correo(nombre, token, correo):
    """
    Envía un correo de recuperación de contraseña usando la API de Brevo.

    Args:
        nombre (str): Nombre del usuario
        token (str): Token de recuperación
        correo (str): Dirección de correo del usuario

    Raises:
        RuntimeError: si la API de Brevo responde con un error
    """
    enlace_recuperacion = url_for(
        'auth.restablecer_password', 
        token=token,
        _external=True
    )

    api_key = os.environ.get('BREVO_API_KEY')
    if not api_key:
        raise RuntimeError("Falta la variable de entorno BREVO_API_KEY")

    remitente_correo = os.environ.get('BREVO_SENDER_EMAIL')
    remitente_nombre = os.environ.get('BREVO_SENDER_NAME', 'Blog Académico')

    if not remitente_correo:
        raise RuntimeError("Falta la variable de entorno BREVO_SENDER_EMAIL")

    payload = {
        "sender": {
            "name": remitente_nombre,
            "email": remitente_correo
        },
        "to": [
            {"email": correo, "name": nombre}
        ],
        "subject": "Recuperación de contraseña - Blog Académico",
        "htmlContent": f"""
        <h2>Hola {nombre}</h2>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p><a href="{enlace_recuperacion}" 
        style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none;
          border-radius: 5px;">
            Restablecer Contraseña
        </a></p>
        <p>Este enlace expira en 1 hora.</p>
        <p>Si no solicitaste esto, ignora este mensaje.</p>
        """
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    try:
        respuesta = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error de red al contactar la API de Brevo: {e}")

    if respuesta.status_code >= 300:
        raise RuntimeError(
            f"Error al enviar correo con Brevo ({respuesta.status_code}): {respuesta.text}"
        )