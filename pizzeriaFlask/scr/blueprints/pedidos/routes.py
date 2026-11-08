
from datetime import datetime

from flask import Blueprint, jsonify, request
from database import mysql
pedidos_bp = Blueprint(
    'pedidos',
    __name__,
    url_prefix='/api/pedidos'
)


DIAS_SEMANA = {
    'lunes': 2,
    'martes': 3,
    'miercoles': 4,
    'miércoles': 4,
    'jueves': 5,
    'viernes': 6,
    'sabado': 7,
    'sábado': 7,
    'domingo': 1
}

MESES = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'setiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12
}


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


def tabla_existe(cursor, tabla):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (tabla,)
    )
    return cursor.fetchone()[0] > 0


def es_texto_valido(valor):
    return isinstance(valor, str) and valor.strip() != ''


def fecha_valida(dia, mes, anio):
    try:
        datetime(anio, mes, dia)
        return True
    except (ValueError, TypeError):
        return False


def normalizar_subtotal(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if numero < 0:
        return None
    if numero.is_integer():
        return int(numero)
    return numero


def obtener_o_registrar_cliente(cursor, datos_cliente, columnas_cliente):
    """Registra el cliente o recupera uno existente con los mismos datos."""
    nombres = datos_cliente['nombres'].strip()
    direccion = datos_cliente['direccion'].strip()
    telefono = datos_cliente['telefono'].strip()

    if 'idCliente' in columnas_cliente:
        cursor.execute(
            """
            SELECT idCliente
            FROM cliente
            WHERE nombres = %s
              AND direccion = %s
              AND telefono = %s
            """,
            (nombres, direccion, telefono)
        )
        fila = cursor.fetchone()
        if fila is not None:
            return fila[0]

    campos = ['nombres', 'direccion', 'telefono']
    valores = [nombres, direccion, telefono]

    if {'dia', 'mes', 'anio'}.issubset(columnas_cliente):
        hoy = datetime.now()
        campos.extend(['dia', 'mes', 'anio'])
        valores.extend([hoy.day, hoy.month, hoy.year])

    placeholders = ', '.join(['%s'] * len(campos))
    sql = "INSERT INTO cliente ({}) VALUES ({})".format(
        ', '.join(campos), placeholders
    )
    cursor.execute(sql, tuple(valores))
    return cursor.lastrowid


def esquema_normalizado(cursor):
    columnas_pedido = columnas_tabla(cursor, 'pedido')
    return (
        'idCliente' in columnas_pedido
        and tabla_existe(cursor, 'detalle_pedido')
    )


def datos_cliente_respuesta(datos_cliente):
    return {
        'nombres': datos_cliente['nombres'].strip(),
        'direccion': datos_cliente['direccion'].strip(),
        'telefono': datos_cliente['telefono'].strip()
    }


# ==========================================================
# POST: REGISTRAR PEDIDO COMPLETO
# ==========================================================
@pedidos_bp.route('/', methods=['POST'])
def registrar_pedido():
    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'No se recibieron datos del pedido',
                'exito': False
            }), 400

        cliente = datos.get('cliente') or {}
        fecha = datos.get('fecha') or {}
        pizzas = datos.get('pizzas') or []

        # Validar datos del cliente.
        nombres = cliente.get('nombres')
        direccion = cliente.get('direccion')
        telefono = cliente.get('telefono')

        if not all(es_texto_valido(v) for v in [nombres, direccion, telefono]):
            return jsonify({
                'mensaje': 'Los datos del cliente son obligatorios y no pueden estar vacios',
                'exito': False
            }), 400

        telefono_limpio = telefono.strip()
        if len(telefono_limpio) > 15:
            return jsonify({
                'mensaje': 'El telefono no puede exceder 15 caracteres',
                'exito': False
            }), 400

        try:
            dia = int(fecha.get('dia'))
            mes = int(fecha.get('mes'))
            anio = int(fecha.get('anio'))
        except (TypeError, ValueError):
            return jsonify({
                'mensaje': 'La fecha debe contener dia, mes y anio numericos',
                'exito': False
            }), 400

        if not fecha_valida(dia, mes, anio):
            return jsonify({
                'mensaje': 'La fecha proporcionada no es valida',
                'exito': False
            }), 400

        if not isinstance(pizzas, list) or len(pizzas) == 0:
            return jsonify({
                'mensaje': 'Debe existir al menos una pizza en el pedido',
                'exito': False
            }), 400

        pizzas_normalizadas = []

        for pizza in pizzas:
            if not isinstance(pizza, dict):
                return jsonify({
                    'mensaje': 'Cada pizza debe ser un objeto JSON valido',
                    'exito': False
                }), 400

            tamano = pizza.get('tamano') or pizza.get('tamaño')
            ingredientes = pizza.get('ingredientes') or pizza.get('ingrediente')
            cantidad = pizza.get('cantidad') or pizza.get('no_pizzas')
            subtotal = pizza.get('subtotal')

            if not es_texto_valido(tamano) or not es_texto_valido(ingredientes):
                return jsonify({
                    'mensaje': 'Cada pizza debe tener tamano e ingredientes',
                    'exito': False
                }), 400

            try:
                cantidad = int(cantidad)
            except (TypeError, ValueError):
                return jsonify({
                    'mensaje': 'La cantidad de pizzas debe ser un entero mayor que cero',
                    'exito': False
                }), 400

            if cantidad <= 0:
                return jsonify({
                    'mensaje': 'La cantidad de pizzas debe ser mayor que cero',
                    'exito': False
                }), 400

            subtotal_normalizado = normalizar_subtotal(subtotal)
            if subtotal_normalizado is None:
                return jsonify({
                    'mensaje': 'Los subtotales deben ser numericos y no negativos',
                    'exito': False
                }), 400

            pizzas_normalizadas.append({
                'tamano': tamano.strip(),
                'ingredientes': ingredientes.strip(),
                'cantidad': cantidad,
                'subtotal': subtotal_normalizado
            })

        total = sum(p['subtotal'] for p in pizzas_normalizadas)
        if isinstance(total, float) and total.is_integer():
            total = int(total)

        cliente_limpio = {
            'nombres': nombres,
            'direccion': direccion,
            'telefono': telefono
        }

        cursor = mysql.connection.cursor()
        cursor.execute("START TRANSACTION")

        columnas_cliente = columnas_tabla(cursor, 'cliente')
        columnas_pedido = columnas_tabla(cursor, 'pedido')
        normalizado = esquema_normalizado(cursor)

        id_cliente = obtener_o_registrar_cliente(
            cursor, cliente_limpio, columnas_cliente
        )

        if normalizado:
            campos_pedido = ['idCliente', 'dia', 'mes', 'anio', 'totalCosto']
            valores_pedido = [id_cliente, dia, mes, anio, total]

            placeholders = ', '.join(['%s'] * len(campos_pedido))
            sql_pedido = "INSERT INTO pedido ({}) VALUES ({})".format(
                ', '.join(campos_pedido), placeholders
            )
            cursor.execute(sql_pedido, tuple(valores_pedido))
            id_pedido = cursor.lastrowid

            columnas_detalle = columnas_tabla(cursor, 'detalle_pedido')

            for pizza in pizzas_normalizadas:
                campos_detalle = ['idPedido']
                valores_detalle = [id_pedido]

                if 'tamaño' in columnas_detalle:
                    campos_detalle.append('tamaño')
                    valores_detalle.append(pizza['tamano'])
                elif 'tamano' in columnas_detalle:
                    campos_detalle.append('tamano')
                    valores_detalle.append(pizza['tamano'])

                if 'ingrediente' in columnas_detalle:
                    campos_detalle.append('ingrediente')
                    valores_detalle.append(pizza['ingredientes'])
                elif 'ingredientes' in columnas_detalle:
                    campos_detalle.append('ingredientes')
                    valores_detalle.append(pizza['ingredientes'])

                if 'no_pizzas' in columnas_detalle:
                    campos_detalle.append('no_pizzas')
                    valores_detalle.append(pizza['cantidad'])
                elif 'cantidad' in columnas_detalle:
                    campos_detalle.append('cantidad')
                    valores_detalle.append(pizza['cantidad'])

                if 'subtotal' in columnas_detalle:
                    campos_detalle.append('subtotal')
                    valores_detalle.append(pizza['subtotal'])

                placeholders_detalle = ', '.join(['%s'] * len(campos_detalle))
                sql_detalle = "INSERT INTO detalle_pedido ({}) VALUES ({})".format(
                    ', '.join(campos_detalle), placeholders_detalle
                )
                cursor.execute(sql_detalle, tuple(valores_detalle))
        else:
            ids_pedido = []
            for pizza in pizzas_normalizadas:
                sql_legacy = """
                    INSERT INTO pedido
                        (dia, mes, anio, totalCosto, tamaño, ingrediente, no_pizzas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_legacy, (
                    dia, mes, anio, pizza['subtotal'],
                    pizza['tamano'], pizza['ingredientes'], pizza['cantidad']
                ))
                ids_pedido.append(cursor.lastrowid)

            id_pedido = ids_pedido[0] if ids_pedido else None

        mysql.connection.commit()

        respuesta = {
            'mensaje': 'Pedido registrado correctamente. Total a pagar: ${}'.format(total),
            'exito': True,
            'idPedido': id_pedido,
            'cliente': datos_cliente_respuesta(cliente_limpio),
            'fecha': {
                'dia': dia,
                'mes': mes,
                'anio': anio
            },
            'pizzas': [
                {
                    'tamano': p['tamano'],
                    'ingredientes': p['ingredientes'],
                    'cantidad': p['cantidad'],
                    'subtotal': p['subtotal']
                }
                for p in pizzas_normalizadas
            ],
            'total': total
        }

        if not normalizado:
            respuesta['idsPedido'] = ids_pedido
            respuesta['nota'] = (
                'La base de datos actual no cuenta con la estructura normalizada. '
                'Cada pizza se almaceno como un registro independiente de pedido.'
            )

        return jsonify(respuesta), 201

    except Exception as e:
        if mysql.connection is not None:
            mysql.connection.rollback()
        print("ERROR AL REGISTRAR PEDIDO:", repr(e))

        return jsonify({
            'mensaje': 'No se pudo registrar el pedido',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()


@pedidos_bp.route('/', methods=['GET'])
def listar_pedidos():
    cursor = None

    try:
        cursor = mysql.connection.cursor()
        normalizado = esquema_normalizado(cursor)

        if normalizado:
            cursor.execute(
                """
                SELECT p.idPedido, p.idCliente, p.dia, p.mes, p.anio, p.totalCosto,
                       c.nombres, c.direccion, c.telefono
                FROM pedido p
                LEFT JOIN cliente c ON p.idCliente = c.idCliente
                ORDER BY p.idPedido
                """
            )
            filas = cursor.fetchall()
            columnas_pedido = [c[0] for c in cursor.description]

            pedidos = []
            for fila in filas:
                datos = dict(zip(columnas_pedido, fila))

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(no_pizzas), 0) AS cantidadPizzas
                    FROM detalle_pedido
                    WHERE idPedido = %s
                    """,
                    (datos['idPedido'],)
                )
                fila_cantidad = cursor.fetchone()
                cantidad_pizzas = 0
                if fila_cantidad is not None and fila_cantidad[0] is not None:
                    cantidad_pizzas = int(fila_cantidad[0])

                cliente = None
                if datos.get('nombres') is not None:
                    cliente = {
                        'idCliente': datos['idCliente'],
                        'nombres': datos['nombres'],
                        'direccion': datos['direccion'],
                        'telefono': datos['telefono']
                    }

                pedidos.append({
                    'idPedido': datos['idPedido'],
                    'cliente': cliente,
                    'fecha': {
                        'dia': datos['dia'],
                        'mes': datos['mes'],
                        'anio': datos['anio']
                    },
                    'total': datos['totalCosto'],
                    'cantidadPizzas': cantidad_pizzas
                })
        else:
            cursor.execute("SELECT * FROM pedido ORDER BY idPedido")
            filas = cursor.fetchall()

            pedidos = []
            for fila in filas:
                datos = fila_a_diccionario(cursor, fila)
                pedidos.append({
                    'idPedido': datos['idPedido'],
                    'cliente': None,
                    'fecha': {
                        'dia': datos['dia'],
                        'mes': datos['mes'],
                        'anio': datos['anio']
                    },
                    'total': datos['totalCosto'],
                    'cantidadPizzas': datos.get('no_pizzas', 0),
                    'tamano': datos.get('tamaño'),
                    'ingredientes': datos.get('ingrediente')
                })

        return jsonify({
            'pedidos': pedidos,
            'mensaje': 'Consulta de pedidos realizada correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR PEDIDOS:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar los pedidos',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

@pedidos_bp.route('/<int:idPedido>', methods=['GET'])
def obtener_pedido(idPedido):
    cursor = None

    try:
        cursor = mysql.connection.cursor()
        normalizado = esquema_normalizado(cursor)

        if normalizado:
            cursor.execute(
                """
                SELECT p.idPedido, p.idCliente, p.dia, p.mes, p.anio, p.totalCosto,
                       c.nombres, c.direccion, c.telefono
                FROM pedido p
                LEFT JOIN cliente c ON p.idCliente = c.idCliente
                WHERE p.idPedido = %s
                """,
                (idPedido,)
            )
            fila = cursor.fetchone()

            if fila is None:
                return jsonify({
                    'mensaje': 'Pedido no encontrado',
                    'exito': False
                }), 404

            datos = fila_a_diccionario(cursor, fila)

            cursor.execute(
                "SELECT * FROM detalle_pedido WHERE idPedido = %s",
                (idPedido,)
            )
            filas_detalle = cursor.fetchall()
            columnas_detalle = [c[0] for c in cursor.description]

            pizzas = []
            for fila_detalle in filas_detalle:
                detalle = dict(zip(columnas_detalle, fila_detalle))
                pizzas.append({
                    'tamano': detalle.get('tamaño') or detalle.get('tamano'),
                    'ingredientes': detalle.get('ingrediente') or detalle.get('ingredientes'),
                    'cantidad': detalle.get('no_pizzas') or detalle.get('cantidad'),
                    'subtotal': detalle.get('subtotal')
                })

            cliente = None
            if datos.get('nombres') is not None:
                cliente = {
                    'idCliente': datos['idCliente'],
                    'nombres': datos['nombres'],
                    'direccion': datos['direccion'],
                    'telefono': datos['telefono']
                }

            pedido = {
                'idPedido': datos['idPedido'],
                'cliente': cliente,
                'fecha': {
                    'dia': datos['dia'],
                    'mes': datos['mes'],
                    'anio': datos['anio']
                },
                'total': datos['totalCosto'],
                'pizzas': pizzas
            }
        else:
            cursor.execute(
                "SELECT * FROM pedido WHERE idPedido = %s",
                (idPedido,)
            )
            fila = cursor.fetchone()

            if fila is None:
                return jsonify({
                    'mensaje': 'Pedido no encontrado',
                    'exito': False
                }), 404

            datos = fila_a_diccionario(cursor, fila)

            pedido = {
                'idPedido': datos['idPedido'],
                'cliente': None,
                'fecha': {
                    'dia': datos['dia'],
                    'mes': datos['mes'],
                    'anio': datos['anio']
                },
                'total': datos['totalCosto'],
                'pizzas': [
                    {
                        'tamano': datos.get('tamaño'),
                        'ingredientes': datos.get('ingrediente'),
                        'cantidad': datos.get('no_pizzas'),
                        'subtotal': datos.get('totalCosto')
                    }
                ]
            }

        return jsonify({
            'pedido': pedido,
            'mensaje': 'Pedido encontrado correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR PEDIDO:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar el pedido',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()


@pedidos_bp.route('/ventas/dia/<string:dia>', methods=['GET'])
def ventas_por_dia(dia):
    cursor = None

    try:
        dia_normalizado = dia.strip().lower()

        if dia_normalizado not in DIAS_SEMANA:
            return jsonify({
                'mensaje': 'Dia de la semana no valido',
                'exito': False
            }), 400

        dia_mysql = DIAS_SEMANA[dia_normalizado]

        cursor = mysql.connection.cursor()
        normalizado = esquema_normalizado(cursor)

        if normalizado:
            cursor.execute(
                """
                SELECT p.idPedido, p.dia, p.mes, p.anio, p.totalCosto,
                       c.nombres AS nombreCliente
                FROM pedido p
                LEFT JOIN cliente c ON p.idCliente = c.idCliente
                WHERE DAYOFWEEK(
                    STR_TO_DATE(
                        CONCAT(p.anio, '-', LPAD(p.mes, 2, '0'), '-', LPAD(p.dia, 2, '0')),
                        '%%Y-%%m-%%d'
                    )
                ) = %s
                ORDER BY p.idPedido
                """,
                (dia_mysql,)
            )
        else:
            cursor.execute(
                """
                SELECT p.idPedido, p.dia, p.mes, p.anio, p.totalCosto,
                       (SELECT c.nombres FROM cliente c
                        WHERE c.dia = p.dia AND c.mes = p.mes AND c.anio = p.anio
                        ORDER BY c.idCliente DESC LIMIT 1) AS nombres
                FROM pedido p
                WHERE DAYOFWEEK(
                    STR_TO_DATE(
                        CONCAT(p.anio, '-', LPAD(p.mes, 2, '0'), '-', LPAD(p.dia, 2, '0')),
                        '%%Y-%%m-%%d'
                    )
                ) = %s
                ORDER BY p.idPedido
                """,
                (dia_mysql,)
            )

        filas = cursor.fetchall()
        columnas = [c[0] for c in cursor.description]

        ventas = []
        for fila in filas:
            datos = dict(zip(columnas, fila))
            venta = {
                'idPedido': datos['idPedido'],
                'fecha': {
                    'dia': datos['dia'],
                    'mes': datos['mes'],
                    'anio': datos['anio']
                },
                'total': datos['totalCosto'],
                'totalCosto': datos['totalCosto']
            }
            nombre_cliente = datos.get('nombreCliente') or 'Cliente'
            venta['cliente'] = nombre_cliente
            venta['nombre'] = nombre_cliente
            venta['nombreCliente'] = nombre_cliente
            ventas.append(venta)

        total_ventas = sum(v['total'] for v in ventas)

        return jsonify({
            'ventas': ventas,
            'dia': dia_normalizado,
            'totalVentas': total_ventas,
            'cantidadPedidos': len(ventas),
            'mensaje': 'Consulta realizada correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR VENTAS POR DIA:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar las ventas por dia',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()


@pedidos_bp.route('/ventas/mes/<string:mes>', methods=['GET'])
def ventas_por_mes(mes):
    cursor = None

    try:
        mes_normalizado = mes.strip().lower()

        if mes_normalizado not in MESES:
            return jsonify({
                'mensaje': 'Mes no valido',
                'exito': False
            }), 400

        numero_mes = MESES[mes_normalizado]

        cursor = mysql.connection.cursor()
        normalizado = esquema_normalizado(cursor)

        if normalizado:
            cursor.execute(
                """
                SELECT p.idPedido, p.dia, p.mes, p.anio, p.totalCosto,
                       c.nombres AS nombreCliente
                FROM pedido p
                LEFT JOIN cliente c ON p.idCliente = c.idCliente
                WHERE p.mes = %s
                ORDER BY p.idPedido
                """,
                (numero_mes,)
            )
        else:
            cursor.execute(
                """
                SELECT p.idPedido, p.dia, p.mes, p.anio, p.totalCosto,
                       (SELECT c.nombres FROM cliente c
                        WHERE c.dia = p.dia AND c.mes = p.mes AND c.anio = p.anio
                        ORDER BY c.idCliente DESC LIMIT 1) AS nombres
                FROM pedido p
                WHERE p.mes = %s
                ORDER BY p.idPedido
                """,
                (numero_mes,)
            )

        filas = cursor.fetchall()
        columnas = [c[0] for c in cursor.description]

        ventas = []
        for fila in filas:
            datos = dict(zip(columnas, fila))
            venta = {
                'idPedido': datos['idPedido'],
                'fecha': {
                    'dia': datos['dia'],
                    'mes': datos['mes'],
                    'anio': datos['anio']
                },
                'total': datos['totalCosto'],
                'totalCosto': datos['totalCosto']
            }
            nombre_cliente = datos.get('nombreCliente') or 'Cliente'
            venta['cliente'] = nombre_cliente
            venta['nombre'] = nombre_cliente
            venta['nombreCliente'] = nombre_cliente
            ventas.append(venta)

        total_ventas = sum(v['total'] for v in ventas)

        return jsonify({
            'ventas': ventas,
            'mes': mes_normalizado,
            'totalVentas': total_ventas,
            'cantidadPedidos': len(ventas),
            'mensaje': 'Consulta realizada correctamente',
            'exito': True
        }), 200

    except Exception as e:
        print("ERROR AL CONSULTAR VENTAS POR MES:", repr(e))

        return jsonify({
            'mensaje': 'Error al consultar las ventas por mes',
            'exito': False,
            'error': str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
