import os

class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # valor por defecto
    SECRET_KEY = os.getenv('SECRET_KEY')

    DATABASE_HOST = os.getenv('DATABASE_HOST')
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DATABASE_NAME = os.getenv('DATABASE_NAME')
    DATABASE_SSL_CA = None
    DATABASE_PORT = os.getenv('DATABASE_PORT')

    IDRIVE_ENDPOINT = os.getenv('IDRIVE_ENDPOINT')
    IDRIVE_ACCESS_KEY = os.getenv('IDRIVE_ACCESS_KEY')
    IDRIVE_SECRET_KEY = os.getenv('IDRIVE_SECRET_KEY')
    IDRIVE_BUCKET = os.getenv('IDRIVE_BUCKET')

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024 
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