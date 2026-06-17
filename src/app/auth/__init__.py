from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='src/app/templates/auth', static_folder='src/app/static', static_url_path='/static')

from . import routes