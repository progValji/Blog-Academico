from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import os
from dotenv import load_dotenv
import pymysql

from src.app.helpers import (
    obtener_conexion,
    salvar_post,
    agrupar_filas_posts,
    salvar_comentario,
    borrar_archivos,
    extraer_archivo,
    obtener_datos_paginados,
    UPLOAD_FOLDER,
)

from src.app.helpers.filters import init_filters

load_dotenv()

app = Flask(__name__, 
            template_folder=os.path.join('src/app', 'templates'),
            static_folder='src/static',
            static_url_path='/static')

init_filters(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite de 16MB por seguridad

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    pagina = request.args.get('pagina', 1, type=int)
    conexion = obtener_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
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

@app.route('/crear_post', methods=['GET', 'POST'])
@login_requerido
def crear_post():
    if request.method == 'POST':
        salvar_post()
        return redirect(url_for('index'))
    return render_template("crear_post.html", titulo="Crea Un Post")

@app.route('/visualizar_post/<int:post_id>')
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

@app.route('/editar_post/<int:post_id>', methods=['POST'])
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

@app.route('/eliminar_post/<int:post_id>', methods=['POST'])
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

@app.route('/ver_texto/<int:media_id>')
def ver_texto(media_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT file_url, nombre_original
        FROM post_media
        WHERE id = %s AND file_type = 'text/plain'
    """, (media_id,))

    archivo = cursor.fetchone()
    cursor.close()
    conexion.close()

    if archivo:
        with open(f"src/static/{archivo['file_url']}", "r", encoding="utf-8") as f:
            contenido = f.read()

        return render_template(
            "ver_texto.html",
            contenido=contenido,
            nombre=archivo['nombre_original']
        )

    return "Archivo no encontrado"

if os.getenv('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False  # Desactiva modo debug

if __name__ == '__main__':
    app.run(debug=True)