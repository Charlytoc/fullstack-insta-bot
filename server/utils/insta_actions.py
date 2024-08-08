import requests
import os


INSTA_ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
def get_conversation_with_user(ig_id: str, user_id: str):
    url = f"https://graph.instagram.com/v20.0/{ig_id}/conversations"
    params = {"user_id": user_id, "access_token": INSTA_ACCESS_TOKEN}
    response = requests.get(url, params=params)
    return response.json()


def get_messages_in_conversation(conversation_id: str):
    url = f"https://graph.instagram.com/v20.0/{conversation_id}"
    params = {"fields": "messages", "access_token": INSTA_ACCESS_TOKEN}
    response = requests.get(url, params=params)
    return response.json()


def get_conversations(ig_id: str):
    url = f"https://graph.instagram.com/v20.0/{ig_id}/conversations"
    params = {"platform": "instagram", "access_token": INSTA_ACCESS_TOKEN}
    response = requests.get(url, params=params)
    return response.json()


def ig_message_parser(message_data: dict, visitor_id: str):
    newMessage = {
        "content": message_data.get("message", ""),
        "role": (
            "user"
            if message_data.get("from", {}).get("id") == visitor_id
            else "assistant"
        ),
    }
    return newMessage

def get_message_info(message_id: str):
    url = f"https://graph.instagram.com/v20.0/{message_id}"
    params = {"fields": "message,to,from", "access_token": INSTA_ACCESS_TOKEN}
    response = requests.get(url, params=params)
    json = response.json()

    return json
