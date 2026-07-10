from . import auth_bp
from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from pymysql import IntegrityError

from ..helpers import(
    obtener_conexion,
    calcular_retraso_exponencial,
    generar_token,
    enviar_correo,
    agrupar_filas_posts,
    obtener_datos_paginados,
    TIEMPO_BLOQUEADO,
    TIEMPO_TOKEN,
    login_requerido,
    borrar_archivos,
    validar_email,
    validar_password
)

@auth_bp.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    mensaje = None
    titulo = "Inicia Sesion"
    conexion = None
    cursor = None
    
    if request.method == 'POST':
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')

        if not correo or not contraseña:
            return render_template('iniciar_sesion.html', mensaje='Completa todos los campos.', titulo=titulo)
        
        if validar_email(correo) is not True:
            return render_template('iniciar_sesion.html', mensaje='Correo no valido.', titulo=titulo)
        
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo, ))
            resultado = cursor.fetchone()

            if not resultado:
                time.sleep(1)
                return render_template('iniciar_sesion.html', mensaje='Usuario o contraseña incorrectas', titulo=titulo)
                
            intentos_fallidos = resultado[5]
            bloqueado_hasta = resultado[7]

            #verificando si la cuenta esta bloqueada
            if bloqueado_hasta:
                if datetime.now() < bloqueado_hasta:
                    # Cuenta aún bloqueada
                    tiempo_restante = (bloqueado_hasta - datetime.now()).total_seconds() / 60
                    mensaje = f'Cuenta bloqueada. Intenta en {int(tiempo_restante)} minutos o solicita recuperación de contraseña.'
                    cursor.close()
                    conexion.close()
                    return render_template('iniciar_sesion.html', mensaje=mensaje, titulo=titulo)
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
        except Exception as e:
            if conexion: conexion.rollback()
            mensaje = 'Ocurrió un error al procesar tu solicitud. Intentalo más tarde.'
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    return render_template('iniciar_sesion.html', mensaje=mensaje, titulo=titulo)

@auth_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    mensaje = None
    titulo = "Registrate"
    conexion = None
    cursor = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')

        if not nombre or not correo or not contraseña:
            return render_template('registrar.html', mensaje='Por favor compelta todos los campos.', titulo=titulo)
        
        if validar_email(correo) is not True:
            return render_template('registrar.html', mensaje='Correo no valido.', titulo=titulo)
        
        mensaje_password = validar_password(contraseña)
        if mensaje_password:
            return render_template('registrar.html', mensaje=mensaje_password, titulo=titulo)

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            contraseña_hash = generate_password_hash(contraseña, method='pbkdf2:sha256')
            cursor.execute("""
                            INSERT INTO usuarios (nombre_usuario, correo, contraseña_hash)
                            VALUES (%s, %s, %s)
                        """, (nombre, correo, contraseña_hash))
            conexion.commit()
            session['user_id'] = cursor.lastrowid
            session['user_name'] = nombre
            return redirect(url_for('perfil'))
        except IntegrityError:
            if conexion: conexion.rollback()
            mensaje = 'Verifica la información e intenta nuevamente'
        except Exception as e:
            if conexion: conexion.rollback()
            mensaje = 'Ocurrió un error al procesar tu solicitud. Intentalo más tarde.'
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    return render_template('registrar.html', mensaje=mensaje, titulo=titulo)

@auth_bp.route('/solicitar_recuperacion', methods=['GET', 'POST'])
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

@auth_bp.route('/restablecer_contraseña/<token>', methods=['GET', 'POST'])
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

@auth_bp.route('/perfil')
@login_requerido
def perfil():
    conexion = obtener_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    pagina = request.args.get('pagina', 1, type=int)
    seccion = request.args.get('seccion', 'datos')
    try:
        cursor.execute("""
            SELECT nombre_usuario, correo, creado_en
            FROM usuarios
            WHERE id = %s
        """, (session['user_id'],))
        datos_personales = cursor.fetchone()

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
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            ) p
            LEFT JOIN usuarios u ON p.user_id = u.id
            LEFT JOIN post_media pm ON p.id = pm.post_id
            ORDER BY p.created_at DESC
            """,
            consulta_total="SELECT COUNT(*) as total FROM posts WHERE user_id = %s",
            params_datos=(session.get('user_id'),),
            params_total=(session.get('user_id'),),
            pagina=pagina
        )
        posts = agrupar_filas_posts(resultado)

        comentarios, paginas_comentarios = obtener_datos_paginados(
            cursor,
            consulta_datos="""
                select c.id, c.post_id, c.user_id, u.nombre_usuario AS autor, c.contenido, c.created_at
                from comentarios c
                INNER JOIN usuarios u ON c.user_id = u.id
                where c.user_id = %s
                order by c.created_at DESC 
                limit %s offset %s
            """,
            consulta_total="select count(*) as total from comentarios c where c.user_id = %s",
            params_datos=(session.get('user_id'),),
            params_total=(session.get('user_id'),),
            pagina=pagina
        )
    finally:
        cursor.close()
        conexion.close()

    return render_template('perfil.html',
                            user_id = session['user_id'],
                            datos_personales= datos_personales,
                            posts = posts,
                            paginas=paginas,
                            comentarios=comentarios,
                            paginas_comentario=paginas_comentarios,
                            seccion=seccion,
                            titulo="Perfil")

@auth_bp.route('/editar_perfil', methods=['POST'])
@login_requerido
def editar_perfil():
    nombre_usuario = request.form.get('nombre_usuario', '').strip()
    correo = request.form.get('correo', '').strip()

    if not nombre_usuario or not correo:
        flash('Por favor completa los campos requeridos', 'error')
        return redirect(url_for('perfil'))

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # Una sola query para verificar duplicados
        cursor.execute(
            """SELECT id, nombre_usuario, correo FROM usuarios 
               WHERE (nombre_usuario = %s OR correo = %s) AND id != %s""",
            (nombre_usuario, correo, session['user_id'])
        )
        conflicto = cursor.fetchone()

        if conflicto:
            _, nombre_en_uso, _ = conflicto
            if nombre_en_uso == nombre_usuario:
                flash('El nombre de usuario ya está en uso.', 'error')
            else:
                flash('Intenta con otro correo.', 'error')
            return redirect(url_for('perfil'))

        cursor.execute(
            "UPDATE usuarios SET nombre_usuario = %s, correo = %s WHERE id = %s",
            (nombre_usuario, correo, session['user_id'])
        )
        conexion.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('auth.perfil'))
    except Exception as e:
        conexion.rollback()
        flash(f'Ocurrió un error: {e}', 'error')
        return redirect(url_for('perfil'))
    finally:
        cursor.close()
        conexion.close()

@auth_bp.route('/cambiar_contrasena', methods=['POST'])
@login_requerido
def cambiar_contrasena():
    contrasena_actual = request.form.get('contrasena_actual', '').strip()
    nueva_contrasena = request.form.get('nueva_contrasena', '').strip()
    confirmar_contrasena = request.form.get('confirmar_contrasena', '').strip()

    if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
        flash('Por favor completa todos los campos.', 'error')
        return redirect(url_for('auth.perfil'))

    if nueva_contrasena != confirmar_contrasena:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('auth.perfil'))

    if nueva_contrasena == contrasena_actual:
        flash('La nueva contraseña debe ser diferente a la actual.', 'error')
        return redirect(url_for('authperfil'))

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT contraseña_hash FROM usuarios WHERE id = %s",
            (session['user_id'],)
        )
        fila = cursor.fetchone()
        if not check_password_hash(fila[0], contrasena_actual):
            flash('La contraseña actual es incorrecta.', 'error')
            return redirect(url_for('auth.perfil'))

        nuevo_hash = generate_password_hash(nueva_contrasena)
        cursor.execute(
            "UPDATE usuarios SET contraseña_hash = %s WHERE id = %s",
            (nuevo_hash, session['user_id'])
        )
        conexion.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('perfil'))
    except Exception as e:
        conexion.rollback()
        flash(f'Ocurrió un error: {e}', 'error')
        return redirect(url_for('auth.perfil'))
    finally:
        cursor.close()
        conexion.close()

@auth_bp.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('user_id', None)
    return redirect(url_for('auth.index'))

@auth_bp.route('/eliminar_cuenta/<int:user_id>', methods=['POST'])
def eliminar_cuenta(user_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            DELETE FROM usuarios WHERE id = %s
        """, (user_id,))
        conexion.commit()
        borrar_archivos(user_id)
        flash('Cuenta eliminada con exito', 'success')
        redirect(url_for("posts.index"))
    finally:
        cursor.close()
        conexion.close()
