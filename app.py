# app.py
from flask import Flask
from routes.ui import ui_bp
from routes.stream import stream_bp
from routes.control import control_bp
from routes.benchmark import bench_bp

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return ('', 204)

app.register_blueprint(ui_bp)
app.register_blueprint(stream_bp)
app.register_blueprint(control_bp)
app.register_blueprint(bench_bp)

if __name__ == '__main__':
    # Inicia el servidor, accesible desde cualquier IP en la red
    app.run(host='0.0.0.0', port=5001, threaded=True)