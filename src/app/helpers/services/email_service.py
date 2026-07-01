"""
Servicio de envío de correos electrónicos
"""
from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)  # se conecta al app cuando esté lista

def enviar_correo(nombre, token, correo):
    """
    Envía un correo de recuperación de contraseña
    
    Args:
        nombre (str): Nombre del usuario
        token (str): Token de recuperación
        correo (str): Dirección de correo del usuario
    """
    enlace_recuperacion = f'http://localhost:5000/restablecer_contraseña/{token}'
    msg = Message(
        subject='Recuperación de contraseña - Blog Académico',
        recipients=[correo],
        html=f"""
        <h2>Hola {nombre},</h2>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p><a href="{enlace_recuperacion}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Restablecer Contraseña
        </a></p>
        <p>Este enlace expira en 1 hora.</p>
        <p>Si no solicitaste esto, ignora este mensaje.</p>
        """
    )
    mail.send(msg)
