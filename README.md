# Documentación del Chatbot con Ollama y Flask
Este proyecto implementa un chatbot inteligente utilizando Flask y Ollama, con integración de Telnyx para mensajería SMS. Las principales características incluyen:

### Funcionalidades Principales

1. **Procesamiento de Mensajes SMS**
   - Recibe mensajes SMS a través de Telnyx
   - Procesa el contenido utilizando IA
   - Reenvía respuestas automáticas

2. **Integración con IA**
   - Utiliza el modelo Mistral de Ollama para generar respuestas
   - Sistema de fallback con respuestas predefinidas
   - Procesamiento de lenguaje natural

3. **Gestión de Base de Datos**
   - Almacenamiento de interacciones con clientes
   - Registro de mensajes y estados
   - Seguimiento de conversaciones

4. **Características Técnicas**
   - API REST con Flask
   - Integración con Telnyx para SMS
   - Base de datos SQLite
   - Sistema de respaldo con respuestas predefinidas
   - Procesamiento de números telefónicos

### Flujo de Trabajo
1. Usuario envía SMS
2. Sistema procesa el mensaje
3. Genera respuesta usando IA
4. Almacena la interacción
5. Reenvía respuesta al número configurado

El sistema está diseñado para ser escalable y mantener un registro completo de todas las interacciones con los usuarios.


## Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de Ollama](#instalación-de-ollama) 
3. [Configuración del Entorno Python](#configuración-del-entorno-python)
4. [Configuración de Telnyx](#configuración-de-telnyx)
5. [Ejecución del Proyecto](#ejecución-del-proyecto)

## Requisitos Previos
- Linux, macOS, o Windows con WSL2
- Python 3.8+
- pip
- Cuenta en Telnyx
- Conexión a Internet

## Instalación de Ollama

1. Instalar Ollama:
   ```bash
   curl -sSL https://ollama.com/install.sh | bash
   ```

2. Verificar el servicio:
   ```bash
   systemctl status ollama
   ```

3. Descargar modelo:
   ```bash
   ollama download mistral
   ```

## Configuración del Entorno Python

1. Crear entorno virtual:
   ```bash
   python3 -m venv venv
   ```

2. Activar entorno:
   ```bash
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Variables de entorno:
   - OLLAMA_API_KEY
   - TELNYX_API_KEY

## Configuración de Telnyx

1. Obtener API Key de Telnyx
2. Configurar webhook para el servidor Flask
3. Verificar conectividad

## Ejecución del Proyecto

1. Inicializar base de datos:
   ```bash
   python manage.py migrate
   ```

2. Iniciar servidor:
   ```bash
   python manage.py runserver
   ```

3. Probar conectividad:
   ```bash
   curl -X POST http://localhost:5005/sms \
   -d "Body=Hola estoy buscando una playa con buen clima en México, ¿cuál recomiendas?" \
   -d "From=+16072222222"
   ```