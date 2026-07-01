from flask import render_template

def registrar_error_handler(app):
    @app.errorhandler(500)
    def error_500(error):
        return render_template('error_500.html', titulo="Error Interno del Servidor"), 500