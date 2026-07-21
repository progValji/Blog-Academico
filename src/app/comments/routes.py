from . import comments_bp
from flask import request, redirect, url_for, flash
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
        flash('Ocurrió un error al eliminar el comentario.', 'danger')
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()
    return redirect(url_for('posts.visualizar_post', post_id=post_id))

@comments_bp.route('/agregar_comentario/<int:post_id>', methods=['POST'])
def agregar_comentario(post_id):
    salvar_comentario(post_id=post_id)
    return redirect(url_for('posts.visualizar_post', post_id=post_id))