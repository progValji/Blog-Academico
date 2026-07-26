import os
from flask import Flask
from dotenv import load_dotenv
from .helpers.filters import init_filters
from .helpers.error_handlers import registrar_error_handler
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from config import config_map

def create_app():
    # Creamos la instancia apuntando correctamente a tus carpetas
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder='static',
                static_url_path='/static')

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.config['SERVER_NAME'] = None 
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    env = os.getenv("FLASK_ENV", "development")

    config = config_map.get(env)
    if config is None:
        raise ValueError(f"Configuración '{env}' no existe")

    app.config.from_object(config)

    # Inicializar filtros personalizados
    init_filters(app)

    # Registrar manejadores de errores
    registrar_error_handler(app)

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