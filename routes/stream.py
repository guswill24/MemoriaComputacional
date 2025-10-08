from flask import Blueprint, Response
import time
from logica_medicion import procesar_datos

stream_bp = Blueprint('stream_bp', __name__)

@stream_bp.route('/stream')
def stream():
    def generate():
        try:
            yield "data: __START__\n\n"
            for linea in procesar_datos():
                msg = str(linea).rstrip("\r\n")
                yield f"data: {msg}\n\n"
                time.sleep(0.3)
        except Exception as e:
            yield f"data: ERROR SERVIDOR: {e}\n\n"
        finally:
            yield "data: __END__\n\n"
    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Connection'] = 'keep-alive'
    return resp

