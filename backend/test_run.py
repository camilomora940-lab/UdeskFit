import requests
import json

base_url = "http://127.0.0.1:8000"
session_response = requests.post(f"{base_url}/api/chat/session", timeout=10)
session_response.raise_for_status()
session = session_response.json()
url = f"{base_url}/api/chat"
payload = {
    "mensaje": "Busco un notebook gamer por menos de 800000",
    "session_id": session["session_id"],
    "session_token": session["session_token"],
}

response = requests.post(url, json=payload)
print(response.json())
