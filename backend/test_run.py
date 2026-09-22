import requests
import json

url = "http://127.0.0.1:8000/api/chat"
payload = {"mensaje": "Busco un notebook gamer por menos de 800000"}

response = requests.post(url, json=payload)
print(response.json())
