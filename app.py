from flask import Flask, request, render_template
import telnyx
import random
import sqlite3
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
# Configurar API key de Telnyx desde variables de entorno
telnyx.api_key = os.getenv('TELNYX_API_KEY')

# Otras configuraciones desde variables de entorno
DB_NAME = os.getenv('DB_NAME', 'crm_pipeline.db')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')

# Agregar configuración de base de datos y funciones relacionadas
DB_NAME = 'crm_pipeline.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT,
            mensaje TEXT,
            respuesta TEXT,
            fecha_contacto TEXT,
            estado TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_cliente(nombre, telefono, mensaje, estado, respuesta=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clientes (nombre, telefono, mensaje, respuesta, fecha_contacto, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, telefono, mensaje, respuesta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), estado))
    conn.commit()
    conn.close()

# Reemplazar la carga del modelo con la configuración de Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"

def generar_respuesta_ia(mensaje):
    try:
        # Verificar si el mensaje menciona vuelos
        if "vuelos" in mensaje.lower():
            return "Para más información sobre vuelos, visita nuestra página web: https://paseotravelclientes.resvoyage.com"
        
        payload = {
            "model": "mistral",
            "prompt": f"""Eres un agente de viajes y asistente de servicio al cliente que responde por SMS.
            Reglas:
            - Responde de forma concisa y directa (ideal entre 100-300 caracteres)
            - Sé profesional pero amigable 
            - No uses emojis
            - Usa español informal pero correcto
            - Si tu respuesta es muy larga, resúmela manteniendo el mensaje principal
            
            Mensaje del cliente: {mensaje}""",
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            respuesta = response.json()['response']
            return respuesta
        else:
            return "Lo sentimos, hay un problema técnico. Intentaremos contactarte pronto."
    except Exception as e:
        print(f"Error al llamar a Ollama: {str(e)}")
        return "Lo sentimos, hay un problema técnico. Intentaremos contactarte pronto."

def limpiar_numero_telefono(numero):
    # Eliminar cualquier carácter que no sea dígito o el signo '+'
    numero = ''.join(c for c in numero if c.isdigit() or c == '+')
    
    # Asegurarse de que el número tenga el formato internacional
    if not numero.startswith('+'):
        numero = '+1' + numero  # Asumiendo que es un número de EE.UU.
    
    # Verificar que el número tenga una longitud válida (E.164: máximo 15 dígitos)
    if len(numero.replace('+', '')) > 15:
        raise ValueError("Número de teléfono demasiado largo")
    
    return numero

# Modificar la ruta SMS
@app.route("/sms", methods=["POST"])
def sms():
    mensaje_entrante = request.form.get("Body")
    telefono_usuario = request.form.get("From")
    
    # Obtener número de destino desde variables de entorno
    NUMERO_DESTINO = os.getenv('TELNYX_TO_NUMBER')
    
    # Generar una respuesta usando la función de IA
    respuesta = generar_respuesta_ia(mensaje_entrante)
    
    # Guardar mensaje y respuesta en la misma fila
    guardar_cliente(
        nombre="Desconocido", 
        telefono=telefono_usuario, 
        mensaje=mensaje_entrante, 
        estado="Respondido",
        respuesta=respuesta
    )
    
    # Enviar la respuesta de IA al número específico
    telnyx.Message.create(
        from_=os.getenv('TELNYX_FROM_NUMBER'),
        to=NUMERO_DESTINO,
        text=respuesta,
        messaging_profile_id=os.getenv('TELNYX_MESSAGING_PROFILE_ID')
    )
    
    return "OK", 200

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    
    return render_template("dashboard.html", clientes=clientes)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5005)
