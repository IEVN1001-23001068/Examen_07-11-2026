from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
from blueprints.clientes.routes import clientes_bp
from blueprints.pedidos.routes import pedidos_bp

from config import config
from database import mysql

app = Flask(__name__)

app.config.from_object(config['development'])

CORS(app, methods=['GET', 'POST', 'OPTIONS'])

mysql.init_app(app)

app.register_blueprint(clientes_bp)
app.register_blueprint(pedidos_bp)


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return jsonify({
        'mensaje': 'Recurso no encontrado',
        'exito': False,
        'error': 'La ruta solicitada no existe'
    }), 404


@app.errorhandler(500)
def error_interno(error):
    return jsonify({
        'mensaje': 'Error interno del servidor',
        'exito': False,
        'error': 'Ocurrio un error inesperado'
    }), 500


@app.route('/')
def inicio():
    return jsonify({
        'mensaje': 'API de Pizzeria Alfredo funcionando correctamente',
        'exito': True
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
