from flask import Blueprint
import os

auth_bp = Blueprint('auth', __name__, 
                    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates', 'auth'))

from . import routes