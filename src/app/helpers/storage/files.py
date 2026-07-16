"""
Utilidades de almacenamiento y gestión de archivos
"""
import os
from ..config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from ..database import obtener_conexion


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


def borrar_archivos(id):
    """
    Elimina todos los archivos asociados a un post de la carpeta de uploads
    
    Args:
        id (int): ID del post cuyos archivos serán eliminados
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT file_url FROM post_media WHERE post_id = %s", (id, ))
        archivos = cursor.fetchall()

        if not archivos:
            return

        for archivo in archivos:
            file_url = archivo[0]

            ruta_archivo = os.path.join(
                UPLOAD_FOLDER,
                os.path.basename(file_url)
            )

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
    except Exception as e:
        print('Error: ', e)
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()


def extraer_archivo(fila):
    """
    Extrae información de archivo desde una fila de resultado de base de datos
    
    Args:
        fila (dict): Fila con datos de post_media
        
    Returns:
        dict: Diccionario con información del archivo
    """
    return {
        'id': fila['media_id'],
        'ruta_archivo': fila['file_url'],
        'nombre_original': fila['nombre_original'],
        'tipo_archivo': fila['file_type']
    }
