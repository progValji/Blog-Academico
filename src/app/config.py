"""
Configuración global del aplicativo
Contiene todas las constantes utilizadas en la aplicación
"""
import os

# Constantes de seguridad
MAX_INTENTOS = 5
TIEMPO_BLOQUEADO = 15  # MINUTOS
TIEMPO_TOKEN = 1  # hora
RETRASO_BASE = 2  # SEGUNDOS

# Constantes Normales
POSTS_POR_PAGINA = 10

# Configuración de subida de archivos
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'src',
    'static'
)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xlsx', 'pptx'}

# Configuración de email
MAIL_CONFIG = {
    'host': os.getenv('DATABASE_HOST'),
    'user': os.getenv('DATABASE_USER'),
    'password': os.getenv('DATABASE_PASSWORD'),
    'database': os.getenv('DATABASE_NAME')
}
