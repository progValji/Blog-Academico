import os
from flask import Flask
from dotenv import load_dotenv
from src.app.helpers import UPLOAD_FOLDER
from src.app.helpers.filters import init_filters

load_dotenv()

def create_app():
    # Creamos la instancia apuntando correctamente a tus carpetas
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder='../static',
                static_url_path='/static')

    # Inicializar filtros personalizados
    init_filters(app)

    # Configuraciones básicas y de seguridad
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite de 16MB

    # Configuración de Email para el entorno académico
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Asegurar que exista el directorio de subidas
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if os.getenv('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False

    # REGISTRO DE BLUEPRINTS
    from .auth.routes import auth_bp
    from .posts.routes import posts_bp

    # Al no ponerle url_prefix a posts_bp, el @posts_bp.route('/') será tu INDEX global
    app.register_blueprint(posts_bp) 
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app