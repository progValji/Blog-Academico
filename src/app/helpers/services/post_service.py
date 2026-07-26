"""
Servicio de gestión de posts
"""
from datetime import datetime
from flask import request, flash, redirect, session, current_app

from ..database import obtener_conexion
from ..storage import extraer_archivo
from ..utils import limpiar_contenido
from .idrive2_service import upload_files_to_idrive

def agrupar_filas_posts(resultados):
    """
    Agrupa filas duplicadas por post_id y consolida sus archivos adjuntos
    Las consultas que hacen LEFT JOIN con post_media devuelven filas duplicadas,
    una por cada archivo. Esta función agrupa esas filas por post.
    
    Args:
        resultados (list): Resultados de la consulta con filas duplicadas
        
    Returns:
        list: Lista de posts con archivos agrupados
    """
    posts_dict = {}
    for fila in resultados:
        post_id = fila['id']

        if post_id not in posts_dict:
            posts_dict[post_id] = dict(fila)  # El resultado ya trae todos los campos
            posts_dict[post_id]['archivos'] = []

        if fila.get('media_id'):
            posts_dict[post_id]['archivos'].append(extraer_archivo(fila))
    return list(posts_dict.values())

def salvar_post():
    """
    Crea un post con sus archivos adjuntos
    Valida contenido, maneja archivos y actualiza la base de datos
    """
    titulo = request.form.get('titulo', '').strip().capitalize()
    contenido = request.form.get('contenido', '').strip()
    archivos = request.files.getlist('adjuntos')

    if not titulo or not contenido:
        flash('El título y el contenido no pueden estar vacíos.', 'warning')
        return redirect(request.url)

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        contenido_limpio = limpiar_contenido(contenido)

        cursor.execute(
            "INSERT INTO posts (user_id, titulo, contenido, created_at) VALUES (%s, %s, %s, %s)",
            (session['user_id'], titulo, contenido_limpio, datetime.now())
        )
        conexion.commit()
        post_id = cursor.lastrowid

        if archivos:
            subidos = []
            errores = []
            subidos, errores = upload_files_to_idrive(archivos, post_id)
            for archivo in subidos:
                cursor.execute(
                    """
                    INSERT INTO post_media (post_id, file_url, file_type, nombre_original)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        archivo['post_id'],
                        archivo['file_url'],
                        archivo['file_type'],
                        archivo['nombre_original']
                    )
                )
                conexion.commit()

                if errores:
                    current_app.logger.warning(
                        f"Fallos al subir adjuntos del post {post_id}: {errores}",
                        exc_info=True
                    )
                    flash(
                        f"{len(errores)} archivo(s) no se pudieron subir. Intenta de nuevo o usa otro formato.",
                        'warning'
                    )

        flash('Has creado el post exitosamente', 'success')
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al guardar el post: {e}", exc_info=True)
        flash('Ocurrió un error al procesar tu solicitud.', 'danger')
        raise
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()
