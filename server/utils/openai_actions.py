import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")


def create_completion_openai(system_prompt, prompt, api_key=api_key, model="gpt-4o-mini"):
    client = OpenAI(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        model=model,
        max_tokens=1800,
    )

    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    system_prompt = "You are a helpful assistant."
    user_prompt = "write a haiku about ai"
    haiku = create_completion_openai(system_prompt, user_prompt)
    print(haiku)
