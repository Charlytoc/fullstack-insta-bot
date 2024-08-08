import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def create_groq_completion(system_prompt, prompt,api_key=GROQ_API_KEY, model="gemma2-9b-it", ):
    client = Groq(
        api_key=api_key,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        max_tokens=2000,
        # response_format={"type": "json_object"}
        
    )

    return chat_completion.choices[0].message.content
