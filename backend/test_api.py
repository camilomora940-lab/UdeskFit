import requests
import json
import uuid

url = "http://127.0.0.1:8000/api/chat"
url_reset = "http://127.0.0.1:8000/api/chat/reset"
headers = {"Content-Type": "application/json"}
session_id = str(uuid.uuid4())[:8]

print("=== Prueba del Recomendador Tech (Con Memoria & Seguridad) ===")
print(f"ID de Sesión: {session_id}")
print("Comandos especiales: 'reiniciar' para borrar memoria, 'salir' para terminar.\n")

while True:
    try:
        mensaje = input("Tú: ")
    except (KeyboardInterrupt, EOFError):
        break

    if mensaje.lower() == 'salir':
        break

    if mensaje.lower() == 'reiniciar':
        try:
            res = requests.post(f"{url_reset}?session_id={session_id}")
            print("\n[Sistema] Memoria conversacional reiniciada.\n")
        except Exception as e:
            print(f"\nError al reiniciar: {e}\n")
        continue

    payload = {
        "mensaje": mensaje,
        "session_id": session_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"\nRecomendador: {response.json().get('respuesta')}\n")
        else:
            print(f"\nError {response.status_code}: {response.text}\n")
    except requests.exceptions.ConnectionError:
        print("\nError: No se pudo conectar. ¿Asegúrate de que el servidor FastAPI esté corriendo en el puerto 8000?\n")

