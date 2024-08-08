from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
import requests
import os
from dotenv import load_dotenv
from server.utils.groq_actions import create_groq_completion
from server.utils.insta_actions import get_conversation_with_user, get_messages_in_conversation, get_message_info, ig_message_parser

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
OWNER_ACCOUNT = """
Name: Charly Chacón
Born: In Venezuela, Santa Bárbara de Barinas.
Age: 25
Birthday: 03 April 1999
Youtube channel url: https://www.youtube.com/channel/UCfsjmxxbyGUSP6nMDJI6k5Q
Linkedin url: https://www.linkedin.com/in/charlytoc/

Work as: Developer, teacher, content creator
ODIO A NICOLAS MADURO
"""

def get_system_prompt(context=""):
    _system_prompt = f"""
    Act as a useful Instagram bot.

    Keep in mind the following information about the owner of the Instagram account: {OWNER_ACCOUNT}


    Context and previous messages: 
    ```latest 5  messages
    {context}
    ```
    
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

app = FastAPI()

@app.get("/authorize", response_class=HTMLResponse)
async def authorize(request: Request, code: str = Query(None)):
    if code:
        if code.endswith('#_'):
            code = code[:-2]
        
        token_response = exchange_code_for_token(code)
        return HTMLResponse(content=f"Token: {token_response}")

    html_content = f"""
    <html>
        <head>
            <title>Instagram Authorization</title>
        </head>
        <body>
            <h1>Authorize with Instagram</h1>
            <a href="https://www.instagram.com/oauth/authorize?client_id=464050633149224&redirect_uri={REDIRECT_URI}&response_type=code&scope=business_basic%2Cbusiness_manage_messages%2Cbusiness_manage_comments%2Cbusiness_content_publish">Authorize</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            message = messaging_event.get("message", {}).get("text", "")
            sender_id = messaging_event.get("sender", {}).get("id", "")
            recipient_id = messaging_event.get("recipient", {}).get("id", "")

            if message and sender_id:
                # Obtener la conversación con el usuario
                conversation = get_conversation_with_user(recipient_id, sender_id)
                if conversation.get("data"):
                    conversation_id = conversation["data"][0]["id"]
                    # Obtener los mensajes anteriores de la conversación
                    previous_messages_data = get_messages_in_conversation(
                        conversation_id
                    )
                    # print(previous_messages_data, "PREV MESSAGE DATA WITH TIMESTAMPS")
                    previous_messages = []
                    # Limitar a los primeros 4 mensajes
                    for msg in previous_messages_data.get("messages", {}).get(
                        "data", []
                    )[:5]:
                        message_data = get_message_info(msg["id"])
                        parsed_message = ig_message_parser(
                            message_data, visitor_id=sender_id
                        )
                        previous_messages.append(parsed_message)

                    # Crear la respuesta con los mensajes anteriores
                    response_message = create_groq_completion(
                        get_system_prompt(context=str(previous_messages)), message
                    )
                    send_response(recipient_id, response_message, sender_id)

    return {"status": "success"}


def send_response(user_id: str, message: str, recipient_id: str):
    url = f"https://graph.instagram.com/{user_id}/messages"
    data = {
        "message": {"text": message+"\n - MESSAGE DE CHARLYBOT"},
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
        "code": code
    }
    print("DATA FOR RESPONSE", data)
    response = requests.post(url, data=data)
    return response.json()

# Mount the static files directory
app.mount("/", StaticFiles(directory="client/dist", html=True), name="static", )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
