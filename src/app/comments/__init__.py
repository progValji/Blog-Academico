from flask import Blueprint

comments_bp = Blueprint('comments', __name__, template_folder='src/app/templates/posts', static_folder='src/app/static', static_url_path='/static')

from . import routes