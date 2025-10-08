from flask import Blueprint, request, Response, jsonify, stream_with_context
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
        def get_int(name, default_value):
            try:
                raw = args.get(name, None)
                if raw is None or raw == '' or str(raw).lower() == 'nan':
                    return default_value
                return int(raw)
            except (TypeError, ValueError):
                return default_value
        bs = get_int('blockSize', 65536)
        params = {
            'filePath': args.get('filePath', 'archivo_grande.txt'),
            'blockSize': bs,
            'pattern': args.get('pattern', 'sequential'),
            'seed': get_int('seed', 42),
            'strideBytes': get_int('strideBytes', bs),
            'hotsetPercent': get_int('hotsetPercent', 10),
            'passes': get_int('passes', 1),
        }
    # Capturamos credenciales y evitamos acceder a `request` desde el generador
    admin_token = request.headers.get('X-Admin-Token') or request.args.get('token') or ''
    pin_env = os.environ.get('ADMIN_PIN', 'raspi')

    def generate(captured_token, captured_pin, captured_params):
        # Control simple por PIN (solo para lanzar benchmarks)
        if captured_token != captured_pin:
            yield "data: FORBIDDEN: Solo el controlador puede ejecutar el benchmark.\n\n"
            yield "data: __END__\n\n"
            return
        try:
            yield "data: __START__\n\n"
            for msg in run_benchmark(captured_params):
                yield f"data: {str(msg).rstrip()}\n\n"
                time.sleep(0.1)
        except Exception as e:
            yield f"data: ERROR SERVIDOR: {e}\n\n"
        finally:
            yield "data: __END__\n\n"
    resp = Response(stream_with_context(generate(admin_token, pin_env, params)), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Connection'] = 'keep-alive'
    return resp

