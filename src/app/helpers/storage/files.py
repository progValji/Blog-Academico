"""
Utilidades de almacenamiento y gestión de archivos
"""
from ..config import ALLOWED_EXTENSIONS


def allowed_file(filename):
    """
    Verifica si un archivo tiene una extensión permitida
    
    Args:
        filename (str): Nombre del archivo a validar
        
    Returns:
        bool: True si la extensión está permitida, False en caso contrario
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extraer_archivo(fila):
    """
    Extrae información de archivo desde una fila de resultado de base de datos
    
    Args:
        fila (dict): Fila con datos de post_media
        
    Returns:
        dict: Diccionario con información del archivo
    """
    from ..services.idrive2_service import generar_url_previsualizacion
    return {
        'id': fila['media_id'],
        'ruta_archivo': generar_url_previsualizacion(fila['file_url']),
        'nombre_original': fila['nombre_original'],
        'tipo_archivo': fila['file_type']
    }
