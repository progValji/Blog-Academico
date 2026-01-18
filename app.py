from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import time
import secrets
from datetime import datetime, timedelta

#Constantes de seguridad
MAX_INTENTOS = 5
TIEMPO_BLOQUEADO = 2 #MINUTOS
RETRASO_BASE = 2 #SEGUNDOS

def calcular_retraso_exponencial(intenos_fallidos):
    if intenos_fallidos == 0: return 0
    return RETRASO_BASE ** (intenos_fallidos - 1)

def obtener_conexion():
    return pymysql.connect(host='localhost',
                        user='root',
                        password='JuanFeliz7',
                        database='blogacademico')

app = Flask(__name__)

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

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        correo = request.form.get('correo')

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute('SELECT id FROM usuarios WHERE correo = %s', (correo))
            resultado = cursor.fetchone()

            if resultado:
                token = secrets.token_urlsafe(32)
                """expira_token = time.time() + 3600

                cursor.execute('UPDATE usuarios SET reset_token = %s, token_expira = %s WHERE correo = %s', (token, expira_token, correo))
                conexion.commit()"""
                # Y luego: enviar email con el enlace de reset
                print('el usuario existe')
                print(token)

            cursor.close()
            conexion.close()
            return render_template('reset_password.html', mensaje = 'Si el correo existe, revisa tu correo electronico')
        except Exception as e: return render_template('reset_password.html', mensaje='Error en el servidor')
    return render_template('reset_password.html')

@app.route('/panel_control')
def panel_control():
    return render_template('panelDeControl.html')

if __name__ == '__main__':
    app.run(debug=True)