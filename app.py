from flask import Flask, request, jsonify
from flask_cors import CORS  # Permite que tu HTML se comunique con el servidor local
import sqlite3

app = Flask(__name__)
CORS(app)  # Evita problemas de bloqueo del navegador (CORS)

DATABASE = 'Supermercado.db'

def inicializar_bd():
    conexion = sqlite3.connect(DATABASE)
    cursor = conexion.cursor()
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
    conexion.commit()
    conexion.close()

@app.route('/api/guardar_pedido', methods=['POST'])
def guardar_pedido():
    datos = request.json
    nombre = datos.get('nombre')
    direccion = datos.get('direccion')
    telefono = datos.get('telefono')
    cantidad = datos.get('cantidad')
    productos = datos.get('productos') # Recibimos el texto
    
    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()
        
        # Insertamos el nuevo campo en la consulta SQL
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

@app.route('/api/obtener_pedidos', methods=['GET'])
def obtener_pedidos():
    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()
        
        # Consulta SQL Ejecutada para leer los registros
        cursor.execute("SELECT id, nombre_cliente, productos, cantidad_total FROM pedidos")
        filas = cursor.fetchall()
        conexion.close()
        
        # Convertimos el resultado en una lista de diccionarios JSON
        lista_pedidos = []
        for fila in filas:
            lista_pedidos.append({
                "id": f"{fila[0]:03d}", # Formato de tres dígitos como 001, 002
                "cliente": fila[1],
                "productos": fila[2],
                "cantidad": fila[3]
            })
            
        return jsonify(lista_pedidos), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    
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


if __name__ == '__main__':
    inicializar_bd()
    app.run(port=8080, debug=True)

# LOGIN ; 
# ENDPOINT: Verificar si un usuario existe y su contraseña es correcta
@app.route('/api/login', methods=['POST'])
def login_usuario():
    # Recibimos el JSON que envía el formulario desde login.html
    datos = request.json
    correo = datos.get('correo')
    password = datos.get('password')

    # Validación en el backend: campos obligatorios
    if not all([correo, password]):
        return jsonify({"status": "error", "mensaje": "Completa todos los campos"}), 400

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        # Buscamos en la tabla un usuario que tenga ESE correo Y ESA contraseña
        query = "SELECT id, nombre FROM usuarios WHERE correo = ? AND password = ?"
        cursor.execute(query, (correo, password))
        usuario = cursor.fetchone()  # Trae solo la primera coincidencia (o None si no hay)
        conexion.close()

        # Si "usuario" tiene datos, las credenciales son correctas
        if usuario:
            return jsonify({
                "status": "success",
                "mensaje": "Bienvenido",
                "nombre": usuario[1]  # usuario[0] sería el id, usuario[1] es el nombre
            }), 200
        else:
            return jsonify({"status": "error", "mensaje": "Correo o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# REGISTRAR ;
# TABLA NUEVA: guarda los usuarios registrados en el sistema.
    # La necesitamos porque registrar.html y login.html van a leer/escribir aquí.
    # UNIQUE en "correo" evita que dos personas se registren con el mismo correo
    # (si lo intentan, SQLite lanza un error que capturamos más abajo en el endpoint)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    # ENDPOINT: Registrar un nuevo usuario en la base de datos
@app.route('/api/registrar', methods=['POST'])
def registrar_usuario():
    # Recibimos el JSON que envía el formulario desde registrar.html
    datos = request.json
    nombre = datos.get('nombre')
    correo = datos.get('correo')
    password = datos.get('password')

    # Validación en el backend (además de la de JS): nunca confiamos solo 
    # en la validación del frontend, porque alguien podría saltarla
    if not all([nombre, correo, password]):
        return jsonify({"status": "error", "mensaje": "Faltan datos"}), 400

    try:
        conexion = sqlite3.connect(DATABASE)
        cursor = conexion.cursor()

        # Consulta SQL para insertar el nuevo usuario en la tabla
        query = "INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)"
        cursor.execute(query, (nombre, correo, password))

        conexion.commit()
        conexion.close()
        return jsonify({"status": "success", "mensaje": "¡Usuario registrado!"}), 201

    # Este error salta específicamente cuando el correo ya existe en la tabla
    # (gracias al UNIQUE que pusimos en la columna "correo")
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "mensaje": "Ese correo ya está registrado"}), 400
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500