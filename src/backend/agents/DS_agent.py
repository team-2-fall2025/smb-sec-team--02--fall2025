import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEEP_SEEK_API_KEY = os.getenv("DEEP_SEEK_API_KEY")
client = OpenAI(api_key=DEEP_SEEK_API_KEY, base_url="https://api.deepseek.com")


def query_deepseek(prompt: str, system_config: str = "You are a helpful assistant") -> str:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_config},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    print("Response from DeepSeek:")
    print(response.usage)
    print(response.choices[0].message.content)
    return response.choices[0].message.content