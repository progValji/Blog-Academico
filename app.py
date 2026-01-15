from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

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
            conexion = pymysql.connect(host='localhost',
                                       user='root',
                                       password='JuanFeliz7',
                                       database='blogacademico')
            cursor = conexion.cursor()
            
            if action == 'iniciar':
                cursor.execute("""
                                SELECT * FROM usuarios WHERE correo = %s
                               """, (correo))
                resultado = cursor.fetchone()
                if resultado and check_password_hash(resultado[3], contraseña): 
                    return redirect(url_for('panel_control'))
                else: mensaje = 'Correo o contraseña incorrectos'
            
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

@app.route('/panel_control')
def panel_control():
    return render_template('panelDeControl.html')

if __name__ == '__main__':
    app.run(debug=True)