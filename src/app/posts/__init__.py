import os
from flask import Blueprint

posts_bp = Blueprint('posts', __name__,
                     template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates', 'posts'))

from . import routes