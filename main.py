from fastapi import FastAPI, Request, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse  # Import RedirectResponse
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
import requests
import traceback

import os
from dotenv import load_dotenv
from server.utils.groq_actions import create_groq_completion
from server.utils.insta_actions import get_conversation_with_user, get_messages_in_conversation, get_message_info, ig_message_parser
from supabase import create_client, Client
from pydantic import BaseModel
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
OWNER_ACCOUNT = """
Act as ChatCare, a professional social media assistant for Medical.

Serve as a virtual medical assistant, ask the user for which is his requirements, pains and more

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
        existing_user = supabase.table('users').select("*").eq("email", user.email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password)
        response = supabase.table('users').insert({
            "email": user.email,
            "password": hashed_password
        }).execute()
        
        return {"message": "User signed up successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    try:
        response = supabase.table('users').select("*").eq("email", user.email).execute()
        
        # Check if the response has an error attribute or if data is empty
        if hasattr(response, 'error') and response.error or not response.data:
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
                        get_system_prompt(context=str(OWNER_ACCOUNT)), message
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
        "code": code
    }
    response = requests.post(url, data=data)
    return response.json()

# Mount the static files directory
app.mount("/", StaticFiles(directory="client/dist", html=True), name="static", )

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
