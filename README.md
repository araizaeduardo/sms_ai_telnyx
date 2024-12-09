# Chatbot SMS con Flask, Vultr y Telnyx
Sistema de chatbot SMS que utiliza Flask como backend, Vultr para procesamiento de IA y Telnyx para mensajería SMS. Incluye un dashboard básico para monitoreo.

## Características Principales

- Procesamiento automático de mensajes SMS vía Telnyx
- Integración con IA de Vultr (modelo mixtral-8x7b)
- Almacenamiento de conversaciones en SQLite
- Dashboard web básico para visualización de mensajes
- Sistema de respaldo con respuestas predefinidas
- Logging detallado de operaciones

## Requisitos

- Python 3.8+
- Cuenta en Telnyx con número SMS configurado
- Cuenta en Vultr con acceso a API de inferencia
- Sistema operativo: Linux, macOS, o Windows con WSL2

## Instalación

1. Clonar el repositorio y crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno en archivo `.env`:
```bash
TELNYX_API_KEY=your_api_key
TELNYX_PUBLIC_KEY=your_public_key
TELNYX_MESSAGING_PROFILE_ID=your_profile_id
TELNYX_FROM_NUMBER=+1234567890
VULTR_CLOUD_INFERENCE_API_KEY=your_vultr_key
DB_NAME=crm_pipeline.db
WEBSITE_URL=https://your-website.com     # URL que se enviará a los clientes en las respuestas automáticas
CONTACT_PHONE=+1234567890                # Número de teléfono para que los clientes se comuniquen
```

## Funcionalidades

### Procesamiento de SMS
- Recepción automática de mensajes
- Validación de números telefónicos
- Respuestas automáticas vía IA
- Fallback para consultas sobre vuelos que incluye la URL configurada en WEBSITE_URL
- Todas las respuestas incluyen el número de contacto configurado en CONTACT_PHONE

### Dashboard Web
- Accesible en ruta principal ('/')
- Visualización básica de mensajes
- Lista simple de conversaciones
- Sin funcionalidades avanzadas de filtrado o búsqueda

### Sistema de Logs
- Registro detallado de operaciones
- Rotación automática de archivos log
- Separación de logs por nivel de importancia

## Ejecución

1. Iniciar el servidor:
```bash
python app.py
```

2. El servidor se iniciará en `http://localhost:8000`

3. Probar webhook (ejemplo):
```bash
curl -X POST http://localhost:8000/sms \
-d "Body=Hola, busco información" \
-d "From=+1234567890"
```

## Estructura del Proyecto
```
.
├── app.py              # Aplicación principal
├── templates/          # Plantillas HTML básicas
│   └── dashboard.html  # Dashboard simple
├── logs/              # Directorio de logs
├── .env               # Variables de entorno
└── requirements.txt    # Dependencias
```

## Notas Importantes

- El dashboard es una implementación básica sin características avanzadas
- Se requiere configuración de webhook en el panel de Telnyx
- Las respuestas de IA están limitadas a 300 tokens
- Sistema de fallback automático para consultas sobre vuelos
- Las URLs y números de contacto son configurables vía variables de entorno