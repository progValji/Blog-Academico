from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import os
from dotenv import load_dotenv
import pymysql

from src.app.helpers import (
    obtener_conexion,
    agrupar_filas_posts,
    salvar_comentario,
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