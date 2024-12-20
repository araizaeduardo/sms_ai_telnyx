from flask import Flask, request, render_template
import telnyx
import random
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os
import openai
import hmac
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
# Configurar API key de Telnyx desde variables de entorno
telnyx.api_key = os.getenv('TELNYX_API_KEY')

# Otras configuraciones desde variables de entorno
DB_NAME = os.getenv('DB_NAME', 'crm_pipeline.db')

# Agregar estas variables cerca del inicio del archivo, junto con las otras configuraciones
WEBSITE_URL = os.getenv('WEBSITE_URL')
CONTACT_PHONE = os.getenv('CONTACT_PHONE')

# Agregar configuración de base de datos y funciones relacionadas

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
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clientes (nombre, telefono, mensaje, respuesta, fecha_contacto, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre, telefono, mensaje, respuesta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), estado))
        conn.commit()

# Reemplazar la configuración de Ollama con Vultr
VULTR_API_KEY = os.getenv('VULTR_CLOUD_INFERENCE_API_KEY')
VULTR_MODEL = os.getenv('VULTR_MODEL', 'mixtral-8x7b')

class VultrInferenceClient:
    def __init__(self, api_key=None):
        """Initialize the Vultr Inference Client"""
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.vultrinference.com/v1"
        )

    def ask_question(self, prompt, model="llama-3.1-70b-instruct-fp8-gh200", max_tokens=300, temperature=0.7):
        """Send a question to the Vultr Inference API"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error en la solicitud: {str(e)}"

def setup_logging():
    """Configure logging to write detailed logs to file and important ones to console"""
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Detailed formatter for file
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # Simpler formatter for console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler (detailed logging)
    log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler (only important messages)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.WARNING)  # Only WARNING and above will show in console
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def generar_respuesta_ia(mensaje):
    logging.info("=== INICIO GENERACIÓN IA ===")
    try:
        logging.info(f"Mensaje a procesar: {mensaje}")
        
        # Verificar si el mensaje menciona vuelos
        if "vuelos" in mensaje.lower():
            return f"Para más información sobre vuelos, visita nuestra página web: {WEBSITE_URL}\nPor favor llámanos al {CONTACT_PHONE} para más información."
        
        # Inicializar cliente de Vultr
        client = VultrInferenceClient(api_key=VULTR_API_KEY)
        
        # Preparar el prompt con las instrucciones del sistema
        prompt = f"""Como agente de viajes y asistente de servicio al cliente que responde por SMS:
        - Responde de forma concisa y directa (ideal entre 100-300 caracteres)
        - Sé profesional pero amigable
        - No uses emojis
        - Usa español informal pero correcto
        - NO incluyas un número de teléfono en tu respuesta, se agregará automáticamente
        
        Pregunta del cliente: {mensaje}"""
        
        logging.info("Enviando solicitud a Vultr...")
        respuesta_ia = client.ask_question(prompt)
        
        # Agregar el número de teléfono a la respuesta
        respuesta_final = f"{respuesta_ia}\nPor favor llámanos al {CONTACT_PHONE} para más información."
        
        logging.info(f"Respuesta final: {respuesta_final}")
        return respuesta_final
            
    except Exception as e:
        logging.error(f"Error en generación IA: {str(e)}")
        logging.error(f"Traceback completo: {traceback.format_exc()}")
        return "Lo sentimos, hay un problema técnico. Por favor llámanos al 818-244-2184 para más información."
    finally:
        logging.info("=== FIN GENERACIÓN IA ===")

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

# Add these new functions and configurations
TELNYX_PUBLIC_KEY = os.getenv('TELNYX_PUBLIC_KEY')  # Add this to your .env file

def verify_telnyx_signature(request_data, signature_header, timestamp_header):
    """Verify that the webhook request came from Telnyx"""
    if not TELNYX_PUBLIC_KEY:
        raise ValueError("TELNYX_PUBLIC_KEY is not configured")
        
    try:
        # Ensure request_data is a string if it's bytes
        if isinstance(request_data, bytes):
            request_data = request_data.decode('utf-8')
            
        # Convert timestamp to integer if it's a string
        if isinstance(timestamp_header, str):
            timestamp_header = int(timestamp_header)
            
        telnyx.Webhook.construct_event(
            request_data,
            signature_header,
            timestamp_header,
            TELNYX_PUBLIC_KEY
        )
        return True
    except ValueError as e:
        print(f"Timestamp conversion failed: {str(e)}")
        return False
    except Exception as e:
        print(f"Webhook verification failed: {str(e)}")
        return False

# Modificar la ruta SMS
@app.route("/sms", methods=["POST"])
def sms():
    logging.info("=== INICIO DE SOLICITUD SMS ===")
    try:
        # Get the raw request data and decode it
        raw_data = request.data.decode('utf-8')
        data = json.loads(raw_data)
        logging.info(f"Received webhook data: {data}")
        
        # Verify it's a message event
        if data.get('data', {}).get('event_type') != 'message.received':
            logging.warning("Not a message event")
            return "Not a message event", 400
            
        # Extract message details
        payload = data['data']['payload']
        mensaje_entrante = payload.get('text', '')
        telefono_usuario = payload.get('from', {}).get('phone_number', '')
        
        logging.info(f"Mensaje: {mensaje_entrante}")
        logging.info(f"Teléfono: {telefono_usuario}")
        
        # Process the message
        telefono_usuario = limpiar_numero_telefono(telefono_usuario)
        respuesta = generar_respuesta_ia(mensaje_entrante)
        
        # Save to database
        guardar_cliente(
            nombre="Desconocido", 
            telefono=telefono_usuario, 
            mensaje=mensaje_entrante, 
            estado="Respondido",
            respuesta=respuesta
        )
        
        # Send response via Telnyx
        telnyx.Message.create(
            from_=os.getenv('TELNYX_FROM_NUMBER'),
            to=telefono_usuario,
            text=respuesta,
            messaging_profile_id=os.getenv('TELNYX_MESSAGING_PROFILE_ID')
        )
        
        return "OK", 200
        
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {str(e)}")
        return "Invalid JSON", 400
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        logging.error(traceback.format_exc())
        return "Error processing webhook", 500

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    
    return render_template("dashboard.html", clientes=clientes)

def validate_config():
    required_vars = [
        'TELNYX_API_KEY',
        'TELNYX_PUBLIC_KEY',
        'VULTR_CLOUD_INFERENCE_API_KEY',
        'TELNYX_FROM_NUMBER',
        'TELNYX_MESSAGING_PROFILE_ID',
        'WEBSITE_URL',
        'CONTACT_PHONE'
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

if __name__ == "__main__":
    setup_logging()
    validate_config()
    init_db()
    app.run(debug=True, port=8000)
