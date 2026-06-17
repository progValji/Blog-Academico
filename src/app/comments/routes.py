from . import comments_bp as app
from flask import request, redirect, url_for, flash
from src.app.helpers import (
    obtener_conexion,
    salvar_comentario,
)

@app.route('/eliminar_comentario/<int:comentario_id>', methods=['POST'])
def eliminar_comentario(comentario_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    next_page = request.args.get('next', 'visualizar_post')

    try:
        cursor.execute("SELECT post_id FROM comentarios WHERE id = %s", (comentario_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            flash('El comentario no existe.', 'error')
            return redirect(url_for('index'))

        post_id = resultado[0]

        cursor.execute("DELETE FROM comentarios WHERE id = %s", (comentario_id,))
        conexion.commit()

        flash('Comentario borrado con éxito', 'success')
    except Exception as e:
        flash('Ocurrió un error al eliminar el comentario.', 'error')
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for(next_page, post_id=post_id))

@app.route('/agregar_comentario/<int:post_id>', methods=['POST'])
def agregar_comentario(post_id):
    salvar_comentario(post_id=post_id)
    return redirect(url_for('visualizar_post', post_id=post_id))