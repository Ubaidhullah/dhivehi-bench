import requests
import json
import os

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
payload = {
    "contents": [{"parts": [{"text": "Hello, world!"}]}]
}
headers = {'Content-Type': 'application/json'}
response = requests.post(url, headers=headers, json=payload)
print(response.status_code)
print(response.text)
