from flask import Blueprint, request, Response, jsonify
import os
import json
import time
from services.benchmark_io import run_benchmark

bench_bp = Blueprint('bench_bp', __name__, url_prefix='/benchmark')

@bench_bp.route('/stream', methods=['GET', 'POST'])
def benchmark_stream():
    if request.method == 'POST':
        params = request.get_json(silent=True) or {}
    else:
        # GET con query params para uso sencillo desde la UI
        args = request.args
        params = {
            'filePath': args.get('filePath', 'archivo_grande.txt'),
            'blockSize': int(args.get('blockSize', 65536)),
            'pattern': args.get('pattern', 'sequential'),
            'seed': int(args.get('seed', 42)),
            'strideBytes': int(args.get('strideBytes', 65536)),
            'hotsetPercent': int(args.get('hotsetPercent', 10)),
            'passes': int(args.get('passes', 1)),
        }
    def generate():
        # Control simple por PIN (solo para lanzar benchmarks)
        admin_pin = request.headers.get('X-Admin-Token') or request.args.get('token') or ''
        pin_env = os.environ.get('ADMIN_PIN', 'raspi')
        if admin_pin != pin_env:
            yield "data: FORBIDDEN: Solo el controlador puede ejecutar el benchmark.\n\n"
            yield "data: __END__\n\n"
            return
        try:
            yield "data: __START__\n\n"
            for msg in run_benchmark(params):
                yield f"data: {str(msg).rstrip()}\n\n"
                time.sleep(0.1)
        except Exception as e:
            yield f"data: ERROR SERVIDOR: {e}\n\n"
        finally:
            yield "data: __END__\n\n"
    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Connection'] = 'keep-alive'
    return resp

