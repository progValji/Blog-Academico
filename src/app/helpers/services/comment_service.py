"""
Servicio de gestión de comentarios
"""
from datetime import datetime
from flask import request, flash, redirect, url_for, session, current_app

from ..database import obtener_conexion
from ..utils import limpiar_contenido


def salvar_comentario(comentario_id=None, post_id=None):
    """
    Crea o actualiza un comentario en un post
    
    Args:
        comentario_id (int, optional): ID del comentario si es edición. None si es creación
        post_id (int, optional): ID del post al que pertenece el comentario
    """
    texto = request.form.get('texto', '').strip()

    if not texto:
        flash('El comentario no puede estar vacío.', 'warning')
        return redirect(url_for('posts.visualizar_post', post_id=post_id))

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        texto_limpio = limpiar_contenido(texto)

        if comentario_id:
            cursor.execute("""
                UPDATE comentarios
                SET contenido = %s
                WHERE id = %s
                """, (texto_limpio, comentario_id))
        else:
            user_id = session.get('user_id')
            cursor.execute("""
                INSERT INTO comentarios (post_id, user_id, contenido, created_at)
                VALUES (%s, %s, %s, %s)
            """, (post_id, user_id, texto_limpio, datetime.now()))
        conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al guardar el comentario: {e}", exc_info=True)
        flash('Ocurrió un error al procesar tu solicitud.', 'danger')
        raise
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()
