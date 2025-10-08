from flask import Blueprint, render_template

ui_bp = Blueprint('ui_bp', __name__)

@ui_bp.route('/')
def index():
    return render_template('index.html')

