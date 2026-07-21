from . import comments_bp
from flask import request, redirect, url_for, flash, current_app
from ..helpers import (
    obtener_conexion,
    salvar_comentario,
)

@comments_bp.route('/eliminar_comentario/<int:comentario_id>', methods=['POST'])
def eliminar_comentario(comentario_id):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT post_id FROM comentarios WHERE id = %s", (comentario_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            flash('El comentario no existe.', 'warning')
            return redirect(url_for('posts.index'))

        post_id = resultado[0]

        cursor.execute("DELETE FROM comentarios WHERE id = %s", (comentario_id,))
        conexion.commit()

        flash('Comentario borrado con éxito', 'success')
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al eliminar el comentario: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()
    return redirect(url_for('posts.visualizar_post', post_id=post_id))

@comments_bp.route('/agregar_comentario/<int:post_id>', methods=['POST'])
def agregar_comentario(post_id):
    try:
        salvar_comentario(post_id=post_id)
    except Exception as e:
        current_app.logger.error(f"Error al agregar el comentario: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
    return redirect(url_for('posts.visualizar_post', post_id=post_id))