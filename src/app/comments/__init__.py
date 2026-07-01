from flask import Blueprint
import os

comments_bp = Blueprint('comments', __name__, 
                        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates', 'comments'))

from . import routes