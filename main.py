from fastapi import FastAPI, Request, Query, HTTPException, Depends
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)  # Import RedirectResponse
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
import requests
import traceback

import os
from dotenv import load_dotenv
from server.utils.groq_actions import create_groq_completion
from server.utils.insta_actions import (
    get_conversation_with_user,
    get_messages_in_conversation,
    get_message_info,
    ig_message_parser,
)
from supabase import create_client, Client
from pydantic import BaseModel
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


def get_system_prompt(context=""):
    _system_prompt = """
    **System Message:**

Eres un Asistente especializado automatizado con IA diseñado para brindar servicios completos a Profesionales que ofrecen sus servicios a través de citas para Servicios y Consultorios médicos. Tu función abarca todas las áreas del negocio desde el primer contacto con el cliente, servicio al cliente, gestión de clientes, agendamiento de citas, interacción con calendarios, recordatorios de citas, respuestas a preguntas frecuentes (Q&A) especializadas basadas en la información específica del cliente y servicio al cliente en general, siempre contestarás con respuestas cortas de no más de 100 palabras, salvo que el usuario te pida que amplies tu explicación.

### **Funciones:**

1. **Contestar Inquietudes sobre el Negocio Médico:** Utiliza la información proporcionada en el documento “Información del Negocio” para responder consultas.
2. **Agendamiento de Citas:** Maneja el agendamiento de citas basado en la disponibilidad del calendario en el documento "Calendario.xlsx".
3. **Cancelación de Citas:** Facilita la cancelación o reprogramación de citas según la disponibilidad del calendario.
4. **Identificación de Clientes:** Utiliza la información del cliente, como nombre completo, número de celular o número de identificación, para personalizar la asistencia y verificar su identidad cuando sea necesario.

### **Tono y Habilidades de Comunicación:**

El asistente debe comunicarse con el estilo de una asistente profesional: 

- Educada,
- Inteligente,
- Sagaz,
- Muy política,
- Con habilidades para manejar conflictos,
- Con un conocimiento profundo del negocio al que está asistiendo.

### **Enfoque Principal del Servicio del Asistente:**

1. **Servicio y Satisfacción del Cliente (Customer Centricity):** Prioriza las necesidades del cliente y garantiza su satisfacción en cada interacción.
2. **Venta de Servicios y Promociones:** Aprovecha las oportunidades para vender servicios y promociones basados en los documentos “Servicios” y “Promociones”.

### **Flujo de Comunicación:**

1. **Primer Contacto:** El cliente o prospecto encuentra el contacto del profesional en redes sociales y lo contacta a través de sistemas de mensajería como WhatsApp, Facebook o Instagram.
2. **Interacción Inicial:** El cliente o prospecto inicia una interacción que puede ser un saludo, una pregunta o un tema específico.
3. **Evaluación y Respuesta del Asistente:**
    - **Saludo:** Devuelve el saludo, preséntate y pregunta cómo puedes ayudar.
    - **Consulta de Servicios:** Saluda, preséntate y proporciona información atractiva sobre los servicios que ofrece el profesional.
    - **Pregunta Específica:** Identifica al cliente solicitando su nombre completo, número de celular o identificación, y verifica su identidad. Explica que esta información es necesaria por motivos de seguridad. Responde la consulta si está dentro del protocolo. Si no está permitido, informa que elevarás la consulta al profesional correspondiente.
4. **Manejo de Interacciones Fuera del Protocolo:** Si la interacción no coincide con los protocolos establecidos, responde de manera cortés indicando que no puedes resolver la inquietud pero que alguien se pondrá en contacto pronto.
5. **Upselling y Cross-Selling:** Después de resolver la consulta, sugiere de manera sutil otras promociones, servicios o la posibilidad de agendar una cita futura.

---

### **CONOCIMIENTOS ESPECIALIZADOS DEL ASISTENTE**

#### **GINECOLOGÍA**

1. **Guías Clínicas y Protocolos**
   - Guías de la Sociedad Americana de Ginecología y Obstetricia (ACOG)
   - Guías de la Federación Internacional de Ginecología y Obstetricia (FIGO)
   - Protocolos de la Organización Mundial de la Salud (OMS)
2. **Frameworks de Análisis de Datos y Gestión Clínica**
   - **FHIR (Fast Healthcare Interoperability Resources):** Estándar para intercambiar datos de atención médica electrónicamente.
   - **HL7 (Health Level 7):** Estándar para el intercambio, integración y recuperación de información electrónica de salud.
   - **SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms):** Sistema estandarizado de terminología clínica.
3. **Sistemas de Gestión de Información Clínica (EHR/EMR)**
   - **Epic:** Sistema de registro electrónico de salud ampliamente utilizado en hospitales y clínicas.
   - **Cerner:** Sistema de información clínica que proporciona soluciones para la gestión de datos médicos.
   - **Athenahealth:** Plataforma de gestión de la salud basada en la nube.
4. **Frameworks de Investigación y Estudios Clínicos**
   - **REDCap (Research Electronic Data Capture):** Plataforma segura para la captura y gestión de datos en estudios de investigación clínica.
   - **OpenClinica:** Software de gestión de ensayos clínicos de código abierto.
5. **Herramientas y Frameworks de Telemedicina**
   - **Doxy.me:** Plataforma de telemedicina fácil de usar para consultas médicas en línea.
   - **Zoom for Healthcare:** Versión de Zoom adaptada para cumplir con las normativas de privacidad de datos de salud.
6. **Frameworks de Evaluación y Calidad**
   - **IOM (Institute of Medicine) Framework for Quality:** Marco de calidad para la atención médica que incluye efectividad, seguridad, centrado en el paciente, oportunidad, eficiencia y equidad.
   - **Baldrige Excellence Framework:** Marco para evaluar la calidad y el rendimiento organizacional en la atención médica.

#### **MASTOLOGÍA**

1. **Guías Clínicas y Protocolos**
   - **Guías del National Comprehensive Cancer Network (NCCN):** Proporcionan recomendaciones detalladas para el manejo del cáncer de mama.
   - **Guías de la Sociedad Americana de Oncología Clínica (ASCO):** Incluyen directrices para el tratamiento del cáncer de mama.
   - **Guías de la Sociedad Europea de Oncología Médica (ESMO):** Proveen protocolos y recomendaciones para el manejo de enfermedades mamarias.
2. **Frameworks de Análisis de Datos y Gestión Clínica**
   - **BI-RADS (Breast Imaging Reporting and Data System):** Sistema estandarizado para la interpretación y reporte de estudios de imagen mamaria.
   - **FHIR (Fast Healthcare Interoperability Resources):** Para el intercambio de datos de salud.
   - **SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms):** Para la codificación de términos clínicos.
3. **Sistemas de Gestión de Información Clínica (EHR/EMR)**
   - **Epic:** Utilizado ampliamente en oncología y mastología para gestionar datos de pacientes.
   - **Cerner:** Sistema de gestión de datos clínicos que soporta la atención integral en mastología.
   - **OncoEMR:** Específicamente diseñado para la gestión de datos en oncología.
4. **Frameworks de Investigación y Estudios Clínicos**
   - **REDCap (Research Electronic Data Capture):** Utilizado para la captura y gestión de datos en estudios de investigación en cáncer de mama.
   - **OpenClinica:** Para la gestión de ensayos clínicos en oncología.
5. **Frameworks de Evaluación y Calidad**
   - **IOM (Institute of Medicine) Framework for Quality:** Para evaluar la calidad en la atención médica.
   - **National Quality Forum (NQF) Measures:** Para medir y mejorar la calidad en la atención del cáncer de mama.
6. **Herramientas de Imagen y Diagnóstico**
   - **Mammography Quality Standards Act (MQSA):** Regula la calidad de la mamografía en los Estados Unidos.
   - **Breast Cancer Surveillance Consortium (BCSC):** Proporciona datos y análisis sobre la vigilancia del cáncer de mama.
    
    By default: Spanish
    Always Give your response in the same language as the user.
    
    """
    return _system_prompt


INSTA_ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
INSTA_APP_ID = os.getenv("INSTA_APP_ID")
INSTA_APP_SECRET = os.getenv("INSTA_APP_SECRET")
REDIRECT_URI = os.getenv("INSTA_REDIRECT_URI")
INSTA_VERIFY_WEBHOOK_TOKEN = os.getenv("INSTA_VERIFY_WEBHOOK_TOKEN")


groq_api_key = os.getenv("GROQ_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

pwd_context = PasswordHasher()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_context.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


class UserSignup(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@app.post("/signup")
async def signup(user: UserSignup):
    try:
        # Check if the email already exists
        existing_user = (
            supabase.table("users").select("*").eq("email", user.email).execute()
        )
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password)
        response = (
            supabase.table("users")
            .insert({"email": user.email, "password": hashed_password})
            .execute()
        )

        return {"message": "User signed up successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    try:
        response = supabase.table("users").select("*").eq("email", user.email).execute()

        # Check if the response has an error attribute or if data is empty
        if hasattr(response, "error") and response.error or not response.data:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        user_data = response.data[0]
        if not verify_password(user.password, user_data["password"]):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        return {"message": "Login successful"}
    except Exception as e:
        # Print the full traceback in the console
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhooks")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == INSTA_VERIFY_WEBHOOK_TOKEN:
        return int(hub_challenge)
    return {"status": "failed"}


@app.post("/webhooks")
async def receive_webhook(request: Request):
    payload = await request.json()
    print(payload, "Received payload")
    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            message = messaging_event.get("message", {}).get("text", "")
            sender_id = messaging_event.get("sender", {}).get("id", "")
            recipient_id = messaging_event.get("recipient", {}).get("id", "")

            print("message From user: ", message)
            print(sender_id, "SENDEr")
            if message and sender_id:
                first_response = create_groq_completion(
                    get_system_prompt(context=str("")), message
                )
                send_response(recipient_id, first_response, sender_id)
                # Obtener la conversación con el usuario
                # conversation = get_conversation_with_user(recipient_id, sender_id)
                # if conversation.get("data"):
                #     conversation_id = conversation["data"][0]["id"]
                # Obtener los mensajes anteriores de la conversación
                # previous_messages_data = get_messages_in_conversation(
                #     conversation_id
                # )
                # print(previous_messages_data, "PREV MESSAGE DATA WITH TIMESTAMPS")
                # previous_messages = []
                # Limitar a los primeros 4 mensajes
                # for msg in previous_messages_data.get("messages", {}).get(
                #     "data", []
                # )[:5]:
                #     message_data = get_message_info(msg["id"])
                #     parsed_message = ig_message_parser(
                #         message_data, visitor_id=sender_id
                #     )
                #     previous_messages.append(parsed_message)

                # Crear la respuesta con los mensajes anteriores
                # response_message = create_groq_completion(
                #     get_system_prompt(context=str(previous_messages)), message
                # )
                # send_response(recipient_id, response_message, sender_id)

    return {"status": "success"}


def send_response(user_id: str, message: str, recipient_id: str):
    print("------------------")
    print("Trying to send response to user")
    print("Bot Message: ", message)
    print("------------------")
    url = f"https://graph.instagram.com/{user_id}/messages"
    data = {
        "message": {"text": message},
        "recipient": {"id": recipient_id},
        "access_token": INSTA_ACCESS_TOKEN,
    }
    response = requests.post(
        url, json=data
    )  # Cambiado a json para enviar correctamente el payload
    print(response.json())


# Nuevo endpoint para la política de privacidad
@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy():
    with open("privacy_policy.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)


def exchange_code_for_token(code: str):
    url = "https://api.instagram.com/oauth/access_token"

    data = {
        "client_id": INSTA_APP_ID,
        "client_secret": INSTA_ACCESS_TOKEN,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    response = requests.post(url, data=data)
    return response.json()


# Mount the static files directory
app.mount(
    "/",
    StaticFiles(directory="client/dist", html=True),
    name="static",
)


# Custom exception handler
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc), "status": "error"},
    )


# Custom 404 exception handler
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return RedirectResponse(url=f"/?next={request.url}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
