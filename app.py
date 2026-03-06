from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql
import time
import secrets
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
from functools import wraps
import bleach
import uuid

load_dotenv()

#Constantes de seguridad
MAX_INTENTOS = 5
TIEMPO_BLOQUEADO = 15 #MINUTOS
TIEMPO_TOKEN = 1 #hora
RETRASO_BASE = 2 #SEGUNDOS

#Constantes Normales
POSTS_POR_PAGINA = 10

# Configuración de subida de archivos
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'src',
    'static',
    'uploads',
    'posts'
)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xlsx', 'pptx'}

def calcular_retraso_exponencial(intenos_fallidos):
    if intenos_fallidos == 0: return 0
    return RETRASO_BASE ** (intenos_fallidos - 1)

def generar_token():
    return secrets.token_urlsafe(32)

def obtener_conexion():
    return pymysql.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )

def enviar_correo(nombre, token, correo):
    mail = Mail(app)
    enlace_recuperacion = f'http://localhost:5000/restablecer_contraseña/{token}'
    msg = Message(
        subject='Recuperación de contraseña - Blog Académico',
        recipients=[correo],
        html=f"""
        <h2>Hola {nombre},</h2>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p><a href="{enlace_recuperacion}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Restablecer Contraseña
        </a></p>
        <p>Este enlace expira en 1 hora.</p>
        <p>Si no solicitaste esto, ignora este mensaje.</p>
        """
    )
    mail.send(msg)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def limpiar_contenido(contenido):
    allowed_tags = ['b', 'i', 'u', 'p', 'br', 'a']
    allowed_attributes = {
        'a': ['href', 'title', 'rel', 'target']
    }

    contenido_limpio = bleach.clean(
        contenido,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https'],
        strip=True
    )

    def set_target_blank(attrs, new=False):
        attrs[(None, "target")] = "_blank"
        attrs[(None, "rel")] = "noopener noreferrer"
        return attrs
            
    resultado = bleach.linkify(contenido_limpio, callbacks=[set_target_blank])
    return resultado

def generar_paginas(pagina_actual, total_paginas, rango=2):
    paginas = []

    for p in range(1, total_paginas + 1):
        if (
            p == 1 or
            p == total_paginas or
            abs(p - pagina_actual) <= rango
        ):
            paginas.append(p)
        elif paginas and paginas[-1] != "...":
            paginas.append("...")

    return paginas

app = Flask(__name__, 
            template_folder=os.path.join('src', 'templates'),
            static_folder='src/static',
            static_url_path='/static')

def borrar_archivos(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT file_url FROM post_media WHERE post_id = %s", (id, ))
        archivos = cursor.fetchall()

        if not archivos:
            return

        for archivo in archivos:
            file_url = archivo[0]
            
            ruta_archivo = os.path.join(
                UPLOAD_FOLDER,
                os.path.basename(file_url)
            )

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
    except Exception as e:
        print('Error: ', e)
    finally:
        cursor.close()
        conexion.close()

@app.template_filter('tiempo_relativo')
def tiempo_relativo(fecha):
    ahora = datetime.now()
    diferencia = ahora - fecha

    segundos = diferencia.total_seconds()

    if segundos < 60:
        return f"{int(segundos)} segundos"
    
    minutos = segundos / 60
    if minutos < 60:
        return f"{int(minutos)} minutos"
    
    horas = minutos / 60
    if horas < 24:
        return f"{int(horas)} horas"
    
    if fecha.year == ahora.year:
        return fecha.strftime("%d %b") 
    else:
        return fecha.strftime("%d %b %Y") 

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

def login_requerido(f):
    @wraps(f)
    def  decorated_funcion(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('acceso_denegado.html', titulo="Acceso Denegado")
        return f(*args, **kwargs)
    return decorated_funcion

@app.route('/')
def index():
    pagina = request.args.get('pagina', 1, type=int)
    offset = (pagina - 1) * POSTS_POR_PAGINA
    total_paginas = 0
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
        pm.file_type,
        (
            SELECT COUNT(*) 
            FROM comentarios c 
            WHERE c.post_id = p.id
        ) AS total_comentarios
        FROM posts p
        LEFT JOIN usuarios u ON p.user_id = u.id
        LEFT JOIN post_media pm ON p.id = pm.post_id
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s;
        """, (POSTS_POR_PAGINA, offset))

        resultados = cursor.fetchall()

        posts_dict = {}

        for fila in resultados:
            post_id = fila['id']

            if post_id not in posts_dict:
                posts_dict[post_id] = {
                    'id': fila['id'],
                    'user_id': fila['user_id'],
                    'titulo': fila['titulo'],
                    'contenido': fila['contenido'],
                    'autor_nombre': fila['autor_nombre'],
                    'total_comentarios': fila['total_comentarios'],
                    'created_at': fila['created_at'],
                    'archivos': []
                }

            if fila['media_id']:
                posts_dict[post_id]['archivos'].append({
                    'id': fila['media_id'],
                    'ruta_archivo': fila['file_url'],
                    'nombre_original': fila['nombre_original'],
                    'tipo_archivo': fila['file_type']
                })

        posts = list(posts_dict.values())

        cursor.execute("SELECT COUNT(*) as total FROM posts")
        total_posts = cursor.fetchone()['total']
        total_paginas = (total_posts + POSTS_POR_PAGINA - 1) // POSTS_POR_PAGINA
        paginas = generar_paginas(pagina, total_paginas)

    except Exception as e:
        posts = []
    finally:
        cursor.close()
        conexion.close()
    return render_template(
        'index.html',
        posts=posts,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        titulo="Inicio",
        paginas=paginas,
    )

@app.route('/auth', methods=['GET', 'POST'])
def login():
    mensaje = None
    titulo = "Inicia Sesion"
    
    if request.method == 'POST':
        action = request.form.get('action')
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            
            if action == 'iniciar':
                #buscar usuario
                cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo))
                resultado = cursor.fetchone()

                if not resultado:
                    time.sleep(1)
                    mensaje = 'Usuario o contraseña incorrectas'
                    cursor.close()
                    conexion.close()
                    return render_template('login.html', mensaje=mensaje, titulo=titulo)
                
                intentos_fallidos = resultado[5]
                bloqueado_hasta = resultado[7]

                #verificando si la cuenta esta bloqueada
                if bloqueado_hasta:
                    bloqueado_hasta_dt = datetime.strptime(str(bloqueado_hasta), '%Y-%m-%d %H:%M:%S')
                    if datetime.now() < bloqueado_hasta_dt:
                        # Cuenta aún bloqueada
                        tiempo_restante = (bloqueado_hasta_dt - datetime.now()).total_seconds() / 60
                        mensaje = f'Cuenta bloqueada. Intenta en {int(tiempo_restante)} minutos o solicita recuperación de contraseña.'
                        cursor.close()
                        conexion.close()
                        return render_template('login.html', mensaje=mensaje, titulo=titulo)
                    else:
                        # Tiempo de bloqueo expiró: resetear intentos
                        cursor.execute("""
                            UPDATE usuarios 
                            SET intentos_fallidos = 0, bloqueado_hasta = NULL
                            WHERE id = %s
                        """, (resultado[0]))
                        conexion.commit()
                        intentos_fallidos = 0

                #aplicar retraso segun intentos previos
                retraso = calcular_retraso_exponencial(intentos_fallidos)
                time.sleep(retraso)
                
                # veficiar contraseña
                if check_password_hash(resultado[3], contraseña):
                    #Login exitoso
                    cursor.execute("""
                    UPDATE usuarios
                    SET intentos_fallidos = 0, ultimo_intento = NULL, bloqueado_hasta=NULL
                    WHERE id = %s
                    """, (resultado[0])) #tal vez ultimo intento deberia guardar la fechaYhora
                    session['user_id'] = resultado[0]
                    session['user_name'] = resultado[1]
                    conexion.commit()
                    cursor.close()
                    conexion.close()
                    return redirect(url_for('perfil'))
                else:
                    intentos_fallidos += 1
                    nuevo_bloqueado_hasta = datetime.now() + timedelta(minutes=TIEMPO_BLOQUEADO) if intentos_fallidos >= 5 else None

                    cursor.execute("""
                        UPDATE usuarios
                        SET intentos_fallidos = %s, ultimo_intento = NOW(), bloqueado_hasta = %s
                        WHERE id = %s  
                        """, (intentos_fallidos, nuevo_bloqueado_hasta, resultado[0]))
                    conexion.commit()
                    mensaje = 'Usuario o contraseña incorrectos'
            
            elif action == 'registrar':
                nombre = request.form.get('nombre')
                
                cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
                if cursor.fetchone():
                    mensaje = 'Verifica la información e intenta nuevamente'
                else:
                    contraseña_hash = generate_password_hash(contraseña, method='pbkdf2:sha256')
                    cursor.execute("""
                                    INSERT INTO usuarios (nombre_usuario, correo, contraseña_hash)
                                    VALUES (%s, %s, %s)
                                   """, (nombre, correo, contraseña_hash))
                    conexion.commit()
                    session['user_id'] = cursor.lastrowid
                    session['user_name'] = nombre
                    cursor.close()
                    conexion.close()
                    return redirect(url_for('perfil'))
            
            cursor.close()
            conexion.close()
        
        except Exception as e:
            mensaje = f'Error: {str(e)}'
    
    return render_template('login.html', mensaje=mensaje, titulo=titulo)

@app.route('/solicitar_recuperacion', methods=['GET', 'POST'])
def solicitar_recuperacion():
    mensaje = None
    titulo = "Solicitar Contraseña"
    if request.method == 'POST':
        correo = request.form.get('correo')

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute('SELECT id, nombre_usuario FROM usuarios WHERE correo = %s', (correo))
            resultado = cursor.fetchone()
            respuesta = None

            if resultado:
                usuario_id, nombre_usuario = resultado
                token = generar_token()
                expira_token = datetime.now() + timedelta(hours=TIEMPO_TOKEN)

                cursor.execute('UPDATE usuarios SET reset_token = %s, token_expira = %s WHERE id = %s', (token, expira_token, usuario_id))
                conexion.commit()
                enviar_correo(nombre_usuario, token, correo)
                mensaje = 'Se envio un enlace de recuperacion a tu correo'
            else: mensaje = 'Si el correo existe en nuestro sistema, recibiras un enlace de recuperacion'
            cursor.close()
            conexion.close()
            return render_template('solicitar_recuperacion.html', mensaje =mensaje, titulo=titulo)
        except Exception as e: return render_template('solicitar_recuperacion.html', mensaje=f'Error: {e}' )
    return render_template('solicitar_recuperacion.html', mensaje = mensaje, titulo=titulo)

@app.route('/restablecer_contraseña/<token>', methods=['GET', 'POST'])
def restablecer_contraseña(token):
    mensaje = None
    token_valido = False

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, nombre_usuario, correo FROM usuarios 
            WHERE reset_token = %s AND token_expira > NOW()
        """, (token))
        resultado = cursor.fetchone()
        
        if resultado:
            token_valido = True
            usuario_id = resultado[0]
            
            if request.method == 'POST':
                nueva_contraseña = request.form.get('nueva_contraseña')
                confirmar_contraseña = request.form.get('confirmar_contraseña')
                
                if nueva_contraseña != confirmar_contraseña:
                    mensaje = '❌ Las contraseñas no coinciden ❌'
                else:
                    contraseña_hash = generate_password_hash(nueva_contraseña, method='pbkdf2:sha256')
                    cursor.execute("""
                        UPDATE usuarios 
                        SET contraseña_hash = %s, 
                            reset_token = NULL, 
                            token_expira = NULL,
                            intentos_fallidos = 0,
                            bloqueado_hasta = NULL
                        WHERE id = %s
                    """, (contraseña_hash, usuario_id))
                    conexion.commit()
                    cursor.close()
                    conexion.close()

                    mensaje = '✅ Contraseña actualizada correctamente. Ya puedes iniciar sesión.'
                    return render_template('restablecer_contraseña.html', 
                                         mensaje=mensaje, 
                                         token_valido=False,
                                         exito=True)
        else:
            # Token inválido o expirado
            token_valido = False
            mensaje = 'Token inválido o expirado. Solicita un nuevo enlace de recuperación.'
        
        cursor.close()
        conexion.close()
    except Exception as e: 
        mensaje = f'Error: {e}'
    
    return render_template('restablecer_contraseña.html', mensaje=mensaje, token_valido=token_valido, titulo = "Restablecer Contraseña")

@app.route('/perfil')
@login_requerido
def perfil():
    return render_template('perfil.html',
                            user_name = session['user_name'],
                            user_id = session['user_id'],
                            titulo="Perfil")

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/crear_post', methods=['GET', 'POST'])
@login_requerido
def crear_post():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        contenido = request.form.get('contenido')
        files = request.files.getlist('adjuntos')

        if not titulo or not contenido:
            flash('El titulo y el contenido no pueden estar vacios.', 'error')
            return redirect(request.url)

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            resultado = limpiar_contenido(contenido)

            saved_files = []
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    extension = filename.rsplit('.', 1)[1].lower()
                    unique_name = f"{uuid.uuid4()}.{extension}"

                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(filepath)

                    relative_path = os.path.join('uploads', 'posts', unique_name).replace('\\', '/')
                    print(file.mimetype or extension)
                    saved_files.append((relative_path, file.mimetype or extension, filename))
                elif file and file.filename != '':
                    flash(f'El archivo {file.filename} no tiene un formato permitido.', 'warning')

            sql = """
                INSERT INTO posts (user_id, titulo, contenido, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                session['user_id'],
                titulo,
                resultado,
                datetime.now()
            ))
            conexion.commit()

            post_id = cursor.lastrowid
            if saved_files:
                media_sql = """
                    INSERT INTO post_media (post_id, file_url, file_type, nombre_original)
                    VALUES (%s, %s, %s, %s)
                """
                media_params = [(post_id, path, ftype, nombre_original) for path, ftype, nombre_original in saved_files]
                cursor.executemany(media_sql, media_params)
                conexion.commit()
            flash('¡Tu post ha sido publicado exitosamente!','success')
            
        except Exception as e:
            flash('Ocurrió un error al guardar el post. Inténtalo de nuevo.', 'error')
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conexion' in locals() and conexion:
                conexion.close()
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
            cursor.close()
            conexion.close()
            abort(404)

        post = {
            'id': resultados[0]['id'],
            'titulo': resultados[0]['titulo'],
            'contenido': resultados[0]['contenido'],
            'autor_nombre': resultados[0]['autor_nombre'],
            'created_at': resultados[0]['created_at'],
            'archivos': []
        }

        for fila in resultados:
            if fila['media_id'] is not None:
                post['archivos'].append({
                    'id': fila['media_id'],
                    'ruta_archivo': fila['file_url'],
                    'nombre_original': fila['nombre_original'],
                    'tipo_archivo': fila['file_type']
                })

        cursor.execute("""
        SELECT u.nombre_usuario AS autor, c.contenido, c.created_at
        FROM comentarios c
        INNER JOIN usuarios u ON c.user_id = u.id
        WHERE c.post_id = %s
        ORDER BY c.created_at ASC;
        """, (post_id,))
        comentarios = cursor.fetchall()

        cursor.close()
        conexion.close()

    except Exception as e:
        print("Error:", e)
        abort(500)

    return render_template(
        'visualizar_post.html',
        titulo="Detalles Post",
        post=post,
        comentarios=comentarios,
        user_id=session.get('user_id')
        
    )

@app.route('/eliminar_post/<int:post_id>', methods=['POST'])
def eliminar_post(post_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        borrar_archivos(post_id)
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conexion.commit()
        flash('Post borrado con exito', 'success')
    except:
        flash('Ocurrió un error al guardar el post. Inténtalo de nuevo.', 'error')
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for('index'))

@app.route('/agregar_comentario/<int:post_id>', methods=['POST'])
def agregar_comentario(post_id):
    user_id = session.get('user_id')
    texto = request.form.get('texto', '').strip()

    if not texto:
        flash('El comentario no puede estar vacío.', 'error')
        return redirect(url_for('visualizar_post', post_id=post_id))

    texto_limpio = limpiar_contenido(texto)
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO comentarios (post_id, user_id, contenido, created_at)
            VALUES (%s, %s, %s, %s)
        """, (post_id, user_id, texto_limpio, datetime.now()))
        conexion.commit()
    except Exception as e:
        flash('Ocurrió un error al agregar el comentario.', 'error')
    finally:
        cursor.close()
        conexion.close()

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