"""
Módulo de conexión a base de datos
"""
import pymysql
from flask import current_app

def obtener_conexion():
    """
    Establece una conexión con la base de datos MySQL
    
    Returns:
        pymysql.connection: Conexión a la base de datos
    """
    try:
        return pymysql.connect(
            host=current_app.config['DATABASE_HOST'],
            user=current_app.config['DATABASE_USER'],
            password=current_app.config['DATABASE_PASSWORD'],
            database=current_app.config['DATABASE_NAME'],
            ssl=current_app.config['DATABASE_SSL_CA'],
        )
    except pymysql.MySQLError as e:
        current_app.logger.error(f"Error al conectar con la base de datos: {e}", exc_info=True)
        raise
    except Exception as e:
        current_app.logger.error(f"Error inesperado al intentar conectar a la base de datos: {e}", exc_info=True)
        raise
