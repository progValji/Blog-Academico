import os
from flask import Flask
from dotenv import load_dotenv
from .helpers.filters import init_filters
from .helpers.services.email_service import init_mail
from .helpers.error_handlers import registrar_error_handler
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

from config import config_map

def create_app():
    # Creamos la instancia apuntando correctamente a tus carpetas
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder='static',
                static_url_path='/static')

    # Configuración de Email para el entorno académico
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    env = os.getenv("FLASK_ENV", "development")

    config = config_map.get(env)
    if config is None:
        raise ValueError(f"Configuración '{env}' no existe")

    app.config.from_object(config)

    # Inicializar filtros personalizados
    init_filters(app)

    # Inicializar el servicio de correo electrónico
    init_mail(app)

    # Registrar manejadores de errores
    registrar_error_handler(app)

    if app.config.get('UPLOAD_FOLDER'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Logging ---
    if not app.debug and not app.testing:
        log_dir = os.path.join(app.root_path, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        handler = RotatingFileHandler(
            os.path.join(log_dir, 'blog.log'),
            maxBytes=100000,
            backupCount=3
        )
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [en %(pathname)s:%(lineno)d]'
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.ERROR)

    from .auth.routes import auth_bp
    from .posts.routes import posts_bp
    from .comments.routes import comments_bp

    app.register_blueprint(posts_bp) 
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(comments_bp, url_prefix='/comments')

    return app