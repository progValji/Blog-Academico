"""
Módulo de conexión a base de datos
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    """
    Establece una conexión con la base de datos MySQL
    
    Returns:
        pymysql.connection: Conexión a la base de datos
    """
    return pymysql.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )
