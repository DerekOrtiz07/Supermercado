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