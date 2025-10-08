from flask import Blueprint, jsonify, request
from services.cache_control import read_meminfo_mb, drop_caches
import time
import os

control_bp = Blueprint('control_bp', __name__)

@control_bp.route('/drop_caches', methods=['POST'])
def drop_caches_route():
    admin_pin = os.environ.get('ADMIN_PIN', 'raspi')
    token = request.headers.get('X-Admin-Token') or request.args.get('token') or ''
    if token != admin_pin:
        return jsonify({'ok': False, 'message': 'FORBIDDEN: Solo el controlador puede ejecutar esta acción.'}), 403
    before = read_meminfo_mb()
    ok, msg = drop_caches()
    time.sleep(0.2)
    after = read_meminfo_mb()
    return jsonify({'ok': ok, 'message': msg, 'before': before, 'after': after})

