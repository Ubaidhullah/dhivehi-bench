import os
from google import genai
from dotenv import load_dotenv

load_dotenv(dotenv_path="translation/dhivehi-english-alignment-engine/.env")
client = genai.Client()
for m in client.models.list():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
