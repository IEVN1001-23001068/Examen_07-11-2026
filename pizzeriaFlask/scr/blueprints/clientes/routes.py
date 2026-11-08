
import re
from datetime import datetime

from flask import Blueprint, jsonify, request
from database import mysql

clientes_bp = Blueprint(
    'clientes',
    __name__,
    url_prefix='/api/clientes'
)


def fila_a_diccionario(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def columnas_tabla(cursor, tabla):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (tabla,)
    )
    return {fila[0] for fila in cursor.fetchall()}


def es_texto_valido(valor):
    return isinstance(valor, str) and valor.strip() != ''


def telefono_valido(telefono):
    telefono = telefono.strip()
    if len(telefono) == 0 or len(telefono) > 15:
        return False
    return re.fullmatch(r'[0-9+\-\s()]{7,15}', telefono) is not None


@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    cursor = None

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM cliente ORDER BY idCliente")
        filas = cursor.fetchall()

        clientes = [fila_a_diccionario(cursor, fila) for fila in filas]

        return jsonify({
            'clientes': clientes,
            'mensaje': 'Consulta de clientes realizada correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR CLIENTES:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar los clientes',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

@clientes_bp.route('/<int:idCliente>', methods=['GET'])
def obtener_cliente(idCliente):
    cursor = None

    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM cliente WHERE idCliente = %s",
            (idCliente,)
        )

        fila = cursor.fetchone()

        if fila is None:
            return jsonify({
                'mensaje': 'Cliente no encontrado',
                'exito': False
            }), 404

        cliente = fila_a_diccionario(cursor, fila)

        return jsonify({
            'cliente': cliente,
            'mensaje': 'Cliente encontrado correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR CLIENTE:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar el cliente',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'No se recibieron datos del cliente',
                'exito': False
            }), 400

        nombres = datos.get('nombres')
        direccion = datos.get('direccion')
        telefono = datos.get('telefono')

        if not all(es_texto_valido(v) for v in [nombres, direccion]):
            return jsonify({
                'mensaje': 'Los campos nombres y direccion son obligatorios',
                'exito': False
            }), 400

        if not es_texto_valido(telefono) or not telefono_valido(telefono):
            return jsonify({
                'mensaje': 'El telefono es obligatorio y debe tener un formato valido de hasta 15 caracteres',
                'exito': False
            }), 400

        cursor = mysql.connection.cursor()
        columnas = columnas_tabla(cursor, 'cliente')

        campos = ['nombres', 'direccion', 'telefono']
        valores = [
            nombres.strip(),
            direccion.strip(),
            telefono.strip()
        ]

        if {'dia', 'mes', 'anio'}.issubset(columnas):
            hoy = datetime.now()
            campos.extend(['dia', 'mes', 'anio'])
            valores.extend([hoy.day, hoy.month, hoy.year])

        placeholders = ', '.join(['%s'] * len(campos))
        sql = "INSERT INTO cliente ({}) VALUES ({})".format(
            ', '.join(campos), placeholders
        )

        cursor.execute(sql, tuple(valores))
        mysql.connection.commit()

        nuevo_id = cursor.lastrowid

        return jsonify({
            'mensaje': 'Cliente registrado correctamente',
            'exito': True,
            'cliente': {
                'idCliente': nuevo_id,
                'nombres': nombres.strip(),
                'direccion': direccion.strip(),
                'telefono': telefono.strip()
            }
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR AL REGISTRAR CLIENTE:", repr(e))

        return jsonify({
            'mensaje': 'No se pudo registrar el cliente',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
