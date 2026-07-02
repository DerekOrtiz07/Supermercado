from flask import Flask, request, jsonify
from flask_cors import CORS  # Permite que tu HTML se comunique con el servidor local
import sqlite3

app = Flask(__name__)
CORS(app)  # Evita problemas de bloqueo del navegador (CORS)

DATABASE = 'Supermercado.db'

# ============================================================
# INICIALIZAR BASE DE DATOS
# Aquí se crean TODAS las tablas que usa el proyecto.
# CREATE TABLE IF NOT EXISTS = solo la crea si no existe todavía,
# así que es seguro correr esta función cada vez que arranca el servidor.
# ============================================================
def inicializar_bd():
    conexion = sqlite3.connect(DATABASE)
    cursor = conexion.cursor()

    # Tabla de pedidos (ya la tenían del avance anterior)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente TEXT NOT NULL,
            direccion TEXT NOT NULL,
            telefono TEXT NOT NULL,
            cantidad_total INTEGER NOT NULL,
            productos TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Preparando'
        )
    """)

    # Tabla de usuarios: la necesitan login.html y registrar.html.
    # UNIQUE en "correo" impide que se registren dos personas con el mismo correo.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


# ============================================================
# ENDPOINT: Guardar un pedido nuevo
# ============================================================
@app.route('/api/guardar_pedido', methods=['POST'])
def guardar_pedido():
    datos = request.json
    nombre = datos.get('nombre')
    direccion = datos.get('direccion')
    telefono = datos.get('telefono')
    cantidad = datos.get('cantidad')
    productos = datos.get('productos')

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        query = """
        INSERT INTO pedidos (nombre_cliente, direccion, telefono, cantidad_total, productos) 
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (nombre, direccion, telefono, cantidad, productos))

        conexion.commit()
        conexion.close()
        return jsonify({"status": "success", "mensaje": "¡Pedido completo guardado!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# ENDPOINT: Obtener todos los pedidos (para pedidos.html)
# ============================================================
@app.route('/api/obtener_pedidos', methods=['GET'])
def obtener_pedidos():
    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        # Incluimos "estado" en el SELECT para que pedidos.html
        # pueda pintar el color correcto (Preparando/En Proceso/Enviado)
        cursor.execute("SELECT id, nombre_cliente, productos, cantidad_total, estado FROM pedidos")
        filas = cursor.fetchall()
        conexion.close()

        lista_pedidos = []
        for fila in filas:
            lista_pedidos.append({
                "id": f"{fila[0]:03d}",  # Formato de tres dígitos: 001, 002...
                "cliente": fila[1],
                "productos": fila[2],
                "cantidad": fila[3],
                "estado": fila[4]
            })

        return jsonify(lista_pedidos), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# ENDPOINT: Actualizar el estado de un pedido (Preparando -> En Proceso -> Enviado)
# ============================================================
@app.route('/api/actualizar_estado', methods=['POST'])
def actualizar_estado():
    datos = request.json
    pedido_id = datos.get('id')
    nuevo_estado = datos.get('estado')

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        query = "UPDATE pedidos SET estado = ? WHERE id = ?"
        cursor.execute(query, (nuevo_estado, int(pedido_id)))

        conexion.commit()
        conexion.close()
        return jsonify({"status": "success", "mensaje": "Estado actualizado"}), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# ENDPOINT: Iniciar sesión
# Busca en la tabla "usuarios" un registro que tenga EXACTAMENTE
# ese correo y esa contraseña. Si lo encuentra, el login es válido.
# ============================================================
@app.route('/api/login', methods=['POST'])
def login_usuario():
    datos = request.json
    correo = datos.get('correo')
    password = datos.get('password')

    # Validación en el backend: nunca confiamos solo en la del frontend
    if not all([correo, password]):
        return jsonify({"status": "error", "mensaje": "Completa todos los campos"}), 400

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        query = "SELECT id, nombre FROM usuarios WHERE correo = ? AND password = ?"
        cursor.execute(query, (correo, password))
        usuario = cursor.fetchone()  # None si no hay coincidencia, o una fila si sí
        conexion.close()

        if usuario:
            return jsonify({
                "status": "success",
                "mensaje": "Bienvenido",
                "nombre": usuario[1]  # usuario[0] es el id, usuario[1] es el nombre
            }), 200
        else:
            return jsonify({"status": "error", "mensaje": "Correo o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# ENDPOINT: Registrar un usuario nuevo
# ============================================================
@app.route('/api/registrar', methods=['POST'])
def registrar_usuario():
    datos = request.json
    nombre = datos.get('nombre')
    correo = datos.get('correo')
    password = datos.get('password')

    if not all([nombre, correo, password]):
        return jsonify({"status": "error", "mensaje": "Faltan datos"}), 400

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        query = "INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)"
        cursor.execute(query, (nombre, correo, password))

        conexion.commit()
        conexion.close()
        return jsonify({"status": "success", "mensaje": "¡Usuario registrado!"}), 201

    # Este error salta SOLO cuando el correo ya existe (por el UNIQUE de la tabla)
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "mensaje": "Ese correo ya está registrado"}), 400
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


# ============================================================
# ARRANQUE DEL SERVIDOR
# IMPORTANTE: esto SIEMPRE debe ir al final del archivo,
# después de haber definido TODAS las rutas (@app.route).
# app.run() se queda corriendo para siempre, así que cualquier
# código escrito DESPUÉS de esta línea nunca se ejecutaría.
# ============================================================
if __name__ == '__main__':
    inicializar_bd()
    app.run(port=8080, debug=True)