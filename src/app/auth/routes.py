from . import auth_bp
from flask import render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime, timedelta
import time
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from pymysql import IntegrityError

from ..helpers import(
    obtener_conexion,
    calcular_retraso_exponencial,
    generar_token,
    enviar_correo,
    TIEMPO_BLOQUEADO,
    TIEMPO_TOKEN,
    login_requerido,
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
            flash('Completa los campos necesarios.', 'warning')
            return redirect(url_for('auth.iniciar_sesion'))
        if validar_email(correo) is not True:
            flash('El correo ingresado no es valido', 'warning')
            return redirect(url_for('auth.iniciar_sesion'))
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo, ))
            resultado = cursor.fetchone()

            if not resultado:
                time.sleep(1)
                flash('Usuario o contraseña incorrectas.', 'warning')
                return redirect(url_for('auth.iniciar_sesion'))
                
            intentos_fallidos = resultado[5]
            bloqueado_hasta = resultado[7]

            #verificando si la cuenta esta bloqueada
            if bloqueado_hasta:
                if datetime.now() < bloqueado_hasta:
                    # Cuenta aún bloqueada
                    tiempo_restante = (bloqueado_hasta - datetime.now()).total_seconds() / 60
                    mensaje = f'Cuenta bloqueada. Intenta en {int(tiempo_restante)} minutos o solicita recuperación de contraseña.'
                    flash(mensaje, 'warning')
                    return redirect(url_for('auth.iniciar_sesion'))
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
                flash('Iniciaste sesion de forma correcta.','success')
                return redirect(url_for('auth.perfil'))
            else:
                intentos_fallidos += 1
                nuevo_bloqueado_hasta = datetime.now() + timedelta(minutes=TIEMPO_BLOQUEADO) if intentos_fallidos >= 5 else None
                cursor.execute("""
                    UPDATE usuarios
                    SET intentos_fallidos = %s, ultimo_intento = NOW(), bloqueado_hasta = %s
                    WHERE id = %s  
                    """, (intentos_fallidos, nuevo_bloqueado_hasta, resultado[0]))
                conexion.commit()
                flash('Usuario o contraseña incorrectas.', 'warning')
        except Exception as e:
            if conexion:
                conexion.rollback()
            current_app.logger.error(f"Error al iniciar sesión: {e}", exc_info=True)
            flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
            return redirect(url_for('auth.iniciar_sesion'))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    return render_template('iniciar_sesion.html', titulo=titulo)

@auth_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    mensaje = None
    titulo = "Registrate"
    conexion = None
    cursor = None
    if request.method == 'POST':
        nombre = request.form.get('nombre').capitalize()
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')

        if not nombre or not correo or not contraseña:
            flash('Completa los campos necesarios.', 'warning')
            return redirect(url_for('auth.registrar'))
        if validar_email(correo) is not True:
            flash('Ingresa un correo valido.', 'warning')
            return redirect(url_for('auth.registrar'))
        
        mensaje_password = validar_password(contraseña)
        if mensaje_password:
            flash(mensaje_password, 'warning')
            return redirect(url_for('auth.registrar'))

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
            flash('Registrado con exito.', 'success')
            return redirect(url_for('auth.perfil'))
        except IntegrityError as e:
            if conexion:
                conexion.rollback()
            current_app.logger.warning(f"Error de integridad al registrar usuario: {e}", exc_info=True)
            flash('Verifica la información e intenta nuevamente.', 'warning')
            return redirect(url_for('auth.registrar'))
        except Exception as e:
            if conexion:
                conexion.rollback()
            current_app.logger.error(f"Error al registrar usuario: {e}", exc_info=True)
            flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
            return redirect(url_for('auth.registrar'))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    return render_template('registrar.html', mensaje=mensaje, titulo=titulo)

@auth_bp.route('/solicitar_recuperacion', methods=['GET', 'POST'])
def solicitar_recuperacion():
    titulo = "Solicitar Contraseña"
    if request.method == 'POST':
        correo = request.form.get('correo')

        if not correo:
            flash('Completa el campo necesario.', 'warning')
            return redirect(url_for('auth.solicitar_recuperacion'))
        if validar_email(correo) is not True:
            flash('Correo no válido.', 'warning')
            return redirect(url_for('auth.solicitar_recuperacion'))
        
        conexion = None
        cursor = None
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute('SELECT id, nombre_usuario FROM usuarios WHERE correo = %s', (correo,))
            resultado = cursor.fetchone()

            if resultado:
                usuario_id, nombre_usuario = resultado
                token = generar_token()
                expira_token = datetime.now() + timedelta(hours=TIEMPO_TOKEN)

                cursor.execute('UPDATE usuarios SET reset_token = %s, token_expira = %s WHERE id = %s', (token, expira_token, usuario_id))
                conexion.commit()
                enviar_correo(nombre_usuario, token, correo)

            flash('Si el correo existe en nuestro sistema, recibirás un enlace de recuperación.', 'success')
            return redirect(url_for('auth.solicitar_recuperacion'))
        except RuntimeError as e:
            current_app.logger.error(f"Fallo envío de correo: {e}")
            if conexion: conexion.rollback()
            flash('Fallo el envio de correo. Intenta mas tarde', 'danger')
            return redirect(url_for('auth.solicitar_recuperacion'))
        except Exception as e:
            if conexion:
                conexion.rollback()
            current_app.logger.error(f"Error al solicitar recuperación de contraseña: {e}", exc_info=True)
            flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
            return redirect(url_for('auth.solicitar_recuperacion'))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    return render_template('solicitar_recuperacion.html', titulo=titulo)

@auth_bp.route('/restablecer_password/<token>', methods=['GET', 'POST'])
def restablecer_password(token):
    token_valido = False
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, nombre_usuario, correo FROM usuarios 
            WHERE reset_token = %s AND token_expira > NOW()
        """, (token))
        resultado = cursor.fetchone()

        if not resultado:
            flash('Token inválido o expirado. Solicita un nuevo enlace de recuperación.', 'danger')
            return render_template('restablecer_password.html', token_valido=False, titulo="Restablecer Contraseña")

        token_valido = True
        usuario_id = resultado[0]

        if request.method == 'POST':
            nueva_contraseña = request.form.get('nueva_contraseña')
            confirmar_contraseña = request.form.get('confirmar_contraseña')

            if not nueva_contraseña or len(nueva_contraseña) < 8:
                flash('❌ La contraseña debe tener al menos 8 caracteres', 'warning')
                return render_template('restablecer_password.html', token_valido=True, titulo="Restablecer Contraseña")

            if nueva_contraseña != confirmar_contraseña:
                flash('❌ Las contraseñas no coinciden', 'warning')
                return render_template('restablecer_password.html', token_valido=True, titulo="Restablecer Contraseña")

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

            flash('✅ Contraseña actualizada correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.iniciar_sesion'))
        return render_template('restablecer_password.html', token_valido=True, titulo="Restablecer Contraseña")
    except Exception as e:
        if conexion: conexion.rollback()
        flash('Inténtalo de nuevo más tarde.', 'danger')
        return redirect(url_for('posts.index'))
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

@auth_bp.route('/perfil')
@login_requerido
def perfil():
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT nombre_usuario, correo, creado_en
            FROM usuarios
            WHERE id = %s
        """, (session['user_id']))
        datos_personales = cursor.fetchone()
    except Exception as e:
        current_app.logger.error(f"Error al cargar el perfil: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('posts.index'))
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

    return render_template('perfil.html',
                            user_id = session['user_id'],
                            datos_personales= datos_personales,
                            titulo="Perfil")

@auth_bp.route('/editar_perfil', methods=['POST'])
@login_requerido
def editar_perfil():
    nombre_usuario = request.form.get('nombre_usuario', '').strip()
    correo = request.form.get('correo', '').strip().lower()

    if not nombre_usuario or not correo:
        flash('Por favor completa los campos requeridos', 'warning')
        return redirect(url_for('auth.perfil'))

    if validar_email(correo) is not True:
        flash('El correo ingresado no es valido', 'warning')
        return redirect(url_for('auth.iniciar_sesion'))

    if len(nombre_usuario) > 50 or len(correo) > 100:
        flash('Nombre de usuario o correo demasiado largo.', 'warning')
        return redirect(url_for('auth.perfil'))

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Pre-chequeo (da mensaje amigable, pero no es garantía atómica)
        cursor.execute(
            """SELECT id, nombre_usuario, correo FROM usuarios
               WHERE (nombre_usuario = %s OR correo = %s) AND id != %s""",
            (nombre_usuario, correo, session['user_id'])
        )
        conflicto = cursor.fetchone()

        if conflicto:
            _, nombre_en_uso, correo_en_uso = conflicto
            if nombre_en_uso == nombre_usuario:
                flash('El nombre de usuario ya está en uso.', 'warning')
            elif correo_en_uso == correo:
                flash('Ese correo ya está en uso.', 'warning')
            return redirect(url_for('auth.perfil'))

        cursor.execute(
            "UPDATE usuarios SET nombre_usuario = %s, correo = %s WHERE id = %s",
            (nombre_usuario, correo, session['user_id'])
        )
        conexion.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('auth.perfil'))
    except IntegrityError as e:
        if conexion:
            conexion.rollback()
        current_app.logger.warning(f"Error de integridad al actualizar perfil: {e}", exc_info=True)
        flash('El nombre de usuario o correo ya está en uso.', 'warning')
        return redirect(url_for('auth.perfil'))
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al actualizar el perfil: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('auth.perfil'))
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

@auth_bp.route('/cambiar_contrasena', methods=['POST'])
@login_requerido
def cambiar_contrasena():
    contrasena_actual = request.form.get('contrasena_actual', '')
    nueva_contrasena = request.form.get('nueva_contrasena', '')
    confirmar_contrasena = request.form.get('confirmar_contrasena', '')

    if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
        flash('Por favor completa todos los campos.', 'warning')
        return redirect(url_for('auth.perfil'))

    if nueva_contrasena != confirmar_contrasena:
        flash('Las contraseñas no coinciden.', 'warning')
        return redirect(url_for('auth.perfil'))

    if nueva_contrasena == contrasena_actual:
        flash('La nueva contraseña debe ser diferente a la actual.', 'warning')
        return redirect(url_for('auth.perfil'))

    mensaje_password = validar_password(nueva_contrasena)
    if mensaje_password:
        flash(mensaje_password, 'warning')
        return redirect(url_for('auth.perfil'))

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT contraseña_hash FROM usuarios WHERE id = %s",
            (session['user_id'],)
        )
        fila = cursor.fetchone()

        if not fila:
            flash('No se pudo verificar tu cuenta. Inicia sesión de nuevo.', 'warning')
            session.clear()
            return redirect(url_for('auth.login'))

        if not check_password_hash(fila[0], contrasena_actual):
            flash('La contraseña actual es incorrecta.', 'warning')
            return redirect(url_for('auth.perfil'))

        nuevo_hash = generate_password_hash(nueva_contrasena)
        cursor.execute(
            "UPDATE usuarios SET contraseña_hash = %s WHERE id = %s",
            (nuevo_hash, session['user_id'])
        )
        conexion.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('auth.perfil'))
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al cambiar la contraseña: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('auth.perfil'))
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

@auth_bp.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('user_id', None)
    flash('Cerraste sesión de forma correcta.', 'success')
    return redirect(url_for('posts.index'))

@auth_bp.route('/eliminar_cuenta', methods=['POST'])
@login_requerido
def eliminar_cuenta():
    user_id = session['user_id'] 
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        conexion.commit()
        session.clear()  # cerrar sesión, ya no existe el usuario
        flash('Cuenta eliminada con éxito.', 'success')
        return redirect(url_for('posts.index'))
    except Exception as e:
        if conexion:
            conexion.rollback()
        current_app.logger.error(f"Error al eliminar la cuenta: {e}", exc_info=True)
        flash('No se pudo procesar tu solicitud. Intenta más tarde.', 'danger')
        return redirect(url_for('auth.perfil'))
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()
