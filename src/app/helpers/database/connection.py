"""
Módulo de conexión a base de datos
"""
import pymysql
import os
from dotenv import load_dotenv
from flask import current_app

load_dotenv()


def obtener_conexion():
    """
    Establece una conexión con la base de datos MySQL
    
    Returns:
        pymysql.connection: Conexión a la base de datos
    """
    try:
        return pymysql.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            database=os.getenv('DATABASE_NAME')
        )
    except pymysql.MySQLError as e:
        current_app.logger.error(f"Error al conectar con la base de datos: {e}", exc_info=True)
        raise
    except Exception as e:
        current_app.logger.error(f"Error inesperado al intentar conectar a la base de datos: {e}", exc_info=True)
        raise
