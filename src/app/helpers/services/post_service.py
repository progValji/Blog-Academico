"""
Servicio de gestión de posts
"""
import os
import uuid
from datetime import datetime
from flask import request, flash, redirect, session
from werkzeug.utils import secure_filename

from ..database import obtener_conexion
from ..storage import allowed_file, extraer_archivo
from ..utils import limpiar_contenido
from ..config import UPLOAD_FOLDER


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


def salvar_post(post_id=None):
    """
    Crea o actualiza un post con sus archivos adjuntos
    Valida contenido, maneja archivos y actualiza la base de datos
    
    Args:
        post_id (int, optional): ID del post si es edición. None si es creación
    """
    titulo = request.form.get('titulo', '').strip().capitalize()
    contenido = request.form.get('contenido')
    files = request.files.getlist('adjuntos')

    if not titulo or not contenido:
        flash('El título y el contenido no pueden estar vacíos.', 'warning')
        return redirect(request.url)

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        resultado = limpiar_contenido(contenido)

        if post_id:
            conservar_ids = request.form.getlist('adjuntos_conservar')
            conservar_ids = [int(id) for id in conservar_ids]

            cursor.execute("SELECT id, file_url FROM post_media WHERE post_id = %s", (post_id,))
            adjuntos_actuales = cursor.fetchall()

            # Comparar: los que están en BD pero NO en conservar → eliminar
            for adjunto in adjuntos_actuales:
                if adjunto[0] not in conservar_ids:
                    ruta_completa = os.path.join(UPLOAD_FOLDER, adjunto[1])
                    if os.path.exists(ruta_completa):
                        os.remove(ruta_completa)
                    cursor.execute("DELETE FROM post_media WHERE id = %s", (adjunto[0],))
                    conexion.commit()

        saved_files = []
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                extension = filename.rsplit('.', 1)[1].lower()
                unique_name = f"{uuid.uuid4()}.{extension}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_name)
                file.save(filepath)
                relative_path = os.path.join('uploads', 'posts', unique_name).replace('\\', '/')
                saved_files.append((relative_path, file.mimetype or extension, filename))

        if post_id:
            sql = """
                UPDATE posts 
                SET titulo = %s, contenido = %s 
                WHERE id = %s AND user_id = %s
            """
            cursor.execute(sql, (titulo, resultado, post_id, session['user_id']))
            mensaje = '¡Post actualizado!'
        else:
            sql = """
                INSERT INTO posts (user_id, titulo, contenido, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (session['user_id'], titulo, resultado, datetime.now()))
            post_id = cursor.lastrowid
            mensaje = '¡Post creado!'

        if saved_files:
            media_sql = """
                INSERT INTO post_media (post_id, file_url, file_type, nombre_original)
                VALUES (%s, %s, %s, %s)
            """
            media_params = [(post_id, path, ftype, name) for path, ftype, name in saved_files]
            cursor.executemany(media_sql, media_params)

        conexion.commit()
        flash(mensaje, 'success')
    except Exception as e:
        conexion.rollback()
        flash(f'Ocurrió un error: {str(e)}', 'danger')
    finally:
        cursor.close()
        conexion.close()
