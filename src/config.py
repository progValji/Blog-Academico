import os
from app.helpers import UPLOAD_FOLDER

class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # valor por defecto
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_HOST = os.getenv('DATABASE_HOST')
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DATABASE_NAME = os.getenv('DATABASE_NAME')
    DATABASE_SSL_CA = None

class DevelopmentConfig(Config):
    DEBUG = True
    UPLOAD_FOLDER = UPLOAD_FOLDER
    
class ProductionConfig(Config):
    DEBUG = False
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024 
    UPLOAD_FOLDER = UPLOAD_FOLDER
    DATABASE_SSL_CA = os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__),
                            "..",
                            "certs",
                            "ca.pem"
                        )
                    )

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}