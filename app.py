from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import time
import secrets
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import os

#Constantes de seguridad
MAX_INTENTOS = 5
TIEMPO_BLOQUEADO = 2 #MINUTOS
TIEMPO_TOKEN = 1 #hora
RETRASO_BASE = 2 #SEGUNDOS

def calcular_retraso_exponencial(intenos_fallidos):
    if intenos_fallidos == 0: return 0
    return RETRASO_BASE ** (intenos_fallidos - 1)

def generar_token():
    return secrets.token_urlsafe(32)

def obtener_conexion():
    return pymysql.connect(host='localhost',
                        user='root',
                        password='JuanFeliz7',
                        database='blogacademico')

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


app = Flask(__name__, 
            template_folder=os.path.join('src', 'templates'),
            static_folder='src/static',
            static_url_path='/static')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "jl3184502@gmail.com"
app.config['MAIL_PASSWORD'] = "rryy cmpt ylyu dfik"
app.config['MAIL_DEFAULT_SENDER'] = ('Blog Académico', 'jl3184502@gmail.com')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth', methods=['GET', 'POST'])
def login():
    mensaje = None
    
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
                    return render_template('login.html', mensaje=mensaje)
                
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
                        return render_template('login.html', mensaje=mensaje)
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
                    conexion.commit()
                    cursor.close()
                    conexion.close()
                    return redirect(url_for('panel_control'))
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
                    return redirect(url_for('panel_control'))
            
            cursor.close()
            conexion.close()
        
        except Exception as e:
            mensaje = f'Error: {str(e)}'
    
    return render_template('login.html', mensaje=mensaje)

@app.route('/solicitar_recuperacion', methods=['GET', 'POST'])
def solicitar_recuperacion():
    mensaje = None
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
            return render_template('solicitar_recuperacion.html', mensaje =mensaje)
        except Exception as e: return render_template('solicitar_recuperacion.html', mensaje=f'Error: {e}')
    return render_template('solicitar_recuperacion.html', mensaje = mensaje)

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
    
    return render_template('restablecer_contraseña.html', mensaje=mensaje, token_valido=token_valido)

@app.route('/panel_control')
def panel_control():
    return render_template('panelDeControl.html')

if __name__ == '__main__':
    app.run(debug=True)