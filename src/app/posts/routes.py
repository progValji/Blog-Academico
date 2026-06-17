from . import posts_bp
from flask import render_template, request, redirect, url_for, flash, session, abort
from src.app.helpers import (
    obtener_conexion,
    borrar_archivos,
    salvar_post,
    extraer_archivo,
)
from src.app.helpers.decorators import login_requerido
import pymysql

@posts_bp.route('/crear_post', methods=['GET', 'POST'])
@login_requerido
def crear_post():
    if request.method == 'POST':
        salvar_post()
        return redirect(url_for('index'))
    return render_template("crear_post.html", titulo="Crea Un Post")

@posts_bp.route('/visualizar_post/<int:post_id>')
def visualizar_post(post_id):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT 
                p.*,
                IFNULL(u.nombre_usuario, 'Usuario eliminado') AS autor_nombre,
                pm.id AS media_id,
                pm.file_url,
                pm.nombre_original,
                pm.file_type
            FROM posts p
            LEFT JOIN usuarios u ON p.user_id = u.id
            LEFT JOIN post_media pm ON p.id = pm.post_id
            WHERE p.id = %s
        """, (post_id,))

        resultados = cursor.fetchall()

        if not resultados:
            return render_template('visualizar_post.html',
                                   titulo="Post No Encontrado",
                                   post=None)

        post = {
            'id': resultados[0]['id'],
            'user_id': resultados[0]['user_id'],
            'titulo': resultados[0]['titulo'],
            'contenido': resultados[0]['contenido'],
            'autor_nombre': resultados[0]['autor_nombre'],
            'created_at': resultados[0]['created_at'],
            'archivos': []
        }

        post['archivos'] = [extraer_archivo(fila) for fila in resultados if fila.get('media_id')]

        cursor.execute("""
        SELECT u.nombre_usuario AS autor, c.contenido, c.created_at, c.user_id, c.id
        FROM comentarios c
        INNER JOIN usuarios u ON c.user_id = u.id
        WHERE c.post_id = %s
        ORDER BY c.created_at ASC;
        """, (post_id,))
        comentarios = cursor.fetchall()

    except Exception as e:
        print("Error:", e)
        abort(500)
    finally:
        cursor.close()
        conexion.close()
    return render_template(
        'visualizar_post.html',
        titulo="Detalles Post",
        post=post,
        comentarios=comentarios,
        user_id=session.get('user_id')
    )

@posts_bp.route('/editar_post/<int:post_id>', methods=['POST'])
def editar_post(post_id):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()

        if post is None: abort(404)
        salvar_post(post_id)
        next_url_editar = request.form.get('next', '/')
        if next_url_editar == '/':
            return redirect(url_for('index'))
        else:
            return redirect(next_url_editar)
    finally:
        cursor.close()
        conexion.close()

@posts_bp.route('/eliminar_post/<int:post_id>', methods=['POST'])
def eliminar_post(post_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        borrar_archivos(post_id)
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conexion.commit()
        flash('Post borrado con exito', 'success')
        next_url_eliminar = request.form.get('next', '/')
        if next_url_eliminar == '/':
            return redirect(url_for('index'))
        else:
            return redirect(next_url_eliminar)
    except:
        flash('Ocurrió un error al borrar el post. Inténtalo de nuevo.', 'error')
    finally:
        cursor.close()
        conexion.close()