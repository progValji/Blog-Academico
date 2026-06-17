from functools import wraps
from flask import session, render_template

def login_requerido(f):
    @wraps(f)
    def  decorated_funcion(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('acceso_denegado.html', titulo="Acceso Denegado")
        return f(*args, **kwargs)
    return decorated_funcion