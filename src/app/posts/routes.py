from . import posts_bp
from flask import render_template, request, redirect, url_for, flash, session, current_app
from ..helpers import (
    obtener_conexion,
    salvar_post,
    extraer_archivo,
    agrupar_filas_posts,
    obtener_datos_paginados,
    eliminar_archivos_post_idrive
)
from ..helpers.decorators import login_requerido
import pymysql

@posts_bp.route('/')
def index():
    pagina = request.args.get('pagina', 1, type=int)
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        resultado, paginas = obtener_datos_paginados(
            cursor,
            consulta_datos="""
            SELECT 
                p.*,
                IFNULL(u.nombre_usuario, 'Usuario eliminado') AS autor_nombre,
                pm.id AS media_id,
                pm.file_url,
                pm.nombre_original,
                pm.file_type,
                (
                    SELECT COUNT(*) 
                    FROM comentarios c 
                    WHERE c.post_id = p.id
                ) AS total_comentarios
            FROM (
                SELECT * FROM posts
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            ) p
            LEFT JOIN usuarios u ON p.user_id = u.id
            LEFT JOIN post_media pm ON p.id = pm.post_id
            ORDER BY p.created_at DESC
            """,
            consulta_total="SELECT COUNT(*) as total FROM posts",
            params_datos=(),
            params_total=(),
            pagina=pagina
        )
        posts = agrupar_filas_posts(resultado)
    finally:
        cursor.close()
        conexion.close()
    return render_template(
        'index.html',
        posts=posts,
        paginas=paginas,
        user_id=session.get('user_id'),
        titulo="Inicio",
    )

@posts_bp.route('/crear_post', methods=['GET', 'POST'])
@login_requerido
def crear_post():
    if request.method == 'POST':
        try:
            salvar_post()
        except Exception as e:
            current_app.logger.error(f"Error al crear el post: {e}", exc_info=True)
            flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('posts.index'))
    return render_template("crear_post.html", titulo="Crea Un Post")

@posts_bp.route('/visualizar_post/<int:post_id>')
def visualizar_post(post_id):
    conexion = None
    cursor = None
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
            flash('El post que intentas visualizar no existe.', 'warning')
            return redirect(url_for('posts.index'))

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
        current_app.logger.error(f"Error al visualizar el post: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('posts.index'))
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    return render_template(
        'visualizar_post.html',
        titulo="Detalles Post",
        post=post,
        comentarios=comentarios,
        user_id=session.get('user_id')
    )

@posts_bp.route('/eliminar_post/<int:post_id>', methods=['POST'])
@login_requerido
def eliminar_post(post_id):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        eliminados, error_idrive = eliminar_archivos_post_idrive(post_id)
        if error_idrive:
            flash('Ocurrió un problema al eliminar los archivos adjuntos.', 'warning')
            current_app.logger.error(
                f"Error al eliminar archivos en IDrive del post {post_id}: {error_idrive}"
            )

        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conexion.commit()
        flash('Post borrado con exito', 'success')
        return redirect(url_for('posts.index'))
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al eliminar el post: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()