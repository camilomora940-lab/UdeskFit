import os
import sys
import re
import json
import hashlib
import urllib.request

# Asegurar que el directorio backend esté siempre en sys.path (para despliegue en Render, Railway, Docker)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the new Google GenAI SDK
from google import genai
from google.genai import types

from db_mock import buscar_productos, recargar_catalogo, CATALOGO_PRODUCTOS, recomendar_por_carrera, PERFILES_CARRERAS
from guardrails import validar_mensaje, session_manager

load_dotenv()

app = FastAPI(title="UDeskFit - Recomendador Tech UdeC API")

# Rutas estáticas para despliegue unificado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Habilitar CORS para que el frontend pueda conectarse desde cualquier dominio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente de Gemini
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class ChatRequest(BaseModel):
    mensaje: str
    session_id: str = "default"

@app.get("/")
def read_root():
    """Sirve la aplicación principal recomendador.html en la raíz del servidor."""
    html_path = os.path.join(PROJECT_ROOT, "recomendador.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {
        "status": "ok",
        "message": "UDeskFit API en línea",
        "productos_en_catalogo": len(CATALOGO_PRODUCTOS)
    }

@app.get("/admin")
def read_admin():
    """Sirve el panel de administración admin.html."""
    admin_path = os.path.join(PROJECT_ROOT, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"status": "error", "message": "admin.html no encontrado"}

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "UDeskFit UdeC",
        "productos_en_catalogo": len(CATALOGO_PRODUCTOS),
        "ai_status": "ready" if client else "missing_api_key"
    }

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache_images")
os.makedirs(CACHE_DIR, exist_ok=True)

def detect_mime(data: bytes, url: str) -> str:
    if len(data) >= 12:
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        if data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        if data.startswith(b'RIFF') and b'WEBP' in data[:16]:
            return 'image/webp'
        if b'ftypavif' in data[:32] or b'ftypavis' in data[:32]:
            return 'image/avif'
    # Fallback por extensión en la URL
    lower = url.lower()
    if lower.endswith('.png'):
        return 'image/png'
    if lower.endswith('.jpg') or lower.endswith('.jpeg'):
        return 'image/jpeg'
    if lower.endswith('.webp'):
        return 'image/webp'
    if lower.endswith('.avif'):
        return 'image/avif'
    return 'image/jpeg'

@app.get("/api/imagen-proxy")
def imagen_proxy(url: str):
    """
    Proxy que resuelve el problema de Content-Type: application/octet-stream
    de la CDN de SoloTodo y cachea localmente las imágenes para carga ultra rápida.
    """
    if not url or not url.startswith("https://media.solotodo.com/"):
        raise HTTPException(status_code=400, detail="Solo se permiten URLs de media.solotodo.com")
    
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_path = os.path.join(CACHE_DIR, url_hash)
    meta_path = os.path.join(CACHE_DIR, f"{url_hash}.meta")
    
    # 1. Si ya está en caché local, servir al instante
    if os.path.exists(cache_path) and os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                mime_type = f.read().strip()
            with open(cache_path, 'rb') as f:
                data = f.read()
            return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=2592000"})
        except Exception:
            pass

    # 2. Descargar de SoloTodo con cabeceras de navegador
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.solotodo.cl/",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            mime_type = detect_mime(data, url)
            
            # Guardar en caché
            try:
                with open(cache_path, 'wb') as f:
                    f.write(data)
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(mime_type)
            except Exception:
                pass
                
            return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=2592000"})
    except urllib.error.HTTPError as he:
        raise HTTPException(status_code=he.code, detail=f"SoloTodo devolvió error {he.code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error obteniendo imagen de SoloTodo: {str(e)}")

@app.get("/api/productos")
def listar_productos(categoria: str = None, presupuesto_max: int = None, q: str = None, limit: int = 50):
    """Retorna productos del catálogo SoloTodo filtrados por categoría, presupuesto y búsqueda."""
    res = buscar_productos(categoria=categoria, presupuesto_maximo=presupuesto_max, query=q, limite=limit)
    return {
        "status": "ok",
        "total_en_catalogo": len(CATALOGO_PRODUCTOS),
        "total_encontrados": len(res),
        "productos": res
    }

@app.get("/api/recomendar")
def api_recomendar(carrera: str = "ing_civil_industrial", presupuesto: str = None, categoria: str = None, q: str = None, limit: int = 50):
    """
    Retorna productos reales de SoloTodo clasificados y optimizados para la carrera universitaria
    y presupuesto seleccionados.
    """
    res = recomendar_por_carrera(carrera=carrera, presupuesto=presupuesto, categoria=categoria, query=q, limite=limit)
    return {
        "status": "ok",
        "carrera": carrera,
        "presupuesto": presupuesto,
        "categoria": categoria,
        "total": len(res),
        "productos": res
    }


@app.get("/api/carreras")
def api_carreras():
    """Retorna la lista oficial completa de las 92 carreras UdeC distribuidas en sus 3 campus."""
    return {
        "status": "ok",
        "total": len(PERFILES_CARRERAS),
        "carreras": [
            {
                "id": slug,
                "nombre": prof.get("nombre", slug),
                "campus": prof.get("campus", "Campus Concepción"),
                "url": prof.get("url", "https://admision.udec.cl/carreras-udec/"),
                "min_ram": prof.get("min_ram", 8),
                "gpu_dedicada": prof.get("gpu_dedicada", False),
                "badge": prof.get("badge", "")
            }
            for slug, prof in PERFILES_CARRERAS.items()
        ]
    }


@app.post("/api/admin/sync-solotodo")
def sync_solotodo():
    """Ejecuta la actualización del catálogo desde SoloTodo."""
    try:
        from populate_from_solotodo import populate_database
        db_file = os.path.join(os.path.dirname(__file__), "products_db.json")
        populate_database(db_file)
        total = recargar_catalogo()
        return {"status": "ok", "message": f"Catálogo sincronizado exitosamente con SoloTodo ({total} productos actualizados)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando con SoloTodo: {str(e)}")

@app.post("/api/chat/reset")
def reset_session(session_id: str = "default"):
    """Permite reiniciar el historial de una conversación."""
    if session_id in session_manager._sessions:
        del session_manager._sessions[session_id]
    return {"status": "ok", "message": "Historial reiniciado correctamente."}

@app.post("/api/chat")
def chat(request: ChatRequest):
    if not client:
        return {
            "respuesta": "El servidor está funcionando, pero no se ha configurado la API Key de Gemini. " 
                         "Por favor, añade GEMINI_API_KEY a tu archivo .env en la carpeta backend."
        }
    
    # 1. Filtro local de seguridad y optimización de cuota (Costo $0)
    es_valido, error_guardrail = validar_mensaje(request.mensaje, request.session_id)
    if not es_valido:
        return {"respuesta": error_guardrail}

    try:
        msg_lower = request.mensaje.lower()
        historial_previo = session_manager.get_history(request.session_id)
        
        # Considerar mensaje actual y último mensaje del usuario para contexto
        textos_recientes = msg_lower
        if historial_previo:
            for item in historial_previo[-2:]:
                textos_recientes += " " + item.get("text", "").lower()

        # 2. Detección de Categoría: priorizar siempre el mensaje actual del estudiante
        def detectar_cat(texto):
            if any(w in texto for w in ["calculadora", "casio", "certamen", "certamenes", "calculo", "cientifica"]):
                return "calculadora"
            elif any(w in texto for w in ["tablet", "ipad", "lapiz", "pantalla tactil", "stylus"]):
                return "tablet"
            elif any(w in texto for w in ["monitor", "monitores", "pantalla externa", "segunda pantalla", "display"]):
                return "monitor"
            elif any(w in texto for w in ["mouse", "teclado", "audifono", "audifonos", "periferico", "almacenamiento"]):
                return "periferico"
            elif any(w in texto for w in ["notebook", "laptop", "computador", "portatil", "macbook", "thinkpad", "gamer"]):
                return "notebook"
            return None

        categoria = detectar_cat(msg_lower) or detectar_cat(textos_recientes) or "notebook"

        # 3. Detección de Carrera: priorizar mensaje actual
        carrera_detectada = None
        for cid in PERFILES_CARRERAS.keys():
            alias = cid.replace("ing_civil_", "").replace("ing_", "")
            if alias in msg_lower or cid in msg_lower:
                carrera_detectada = cid
                break
        if not carrera_detectada:
            for cid in PERFILES_CARRERAS.keys():
                alias = cid.replace("ing_civil_", "").replace("ing_", "")
                if alias in textos_recientes or cid in textos_recientes:
                    carrera_detectada = cid
                    break

        # 4. Detección de Presupuesto
        presupuesto_clp = None
        num_match = re.search(r'(\d{1,3}(?:\.\d{3})+|\d{5,8})', request.mensaje.replace('$', ''))
        if num_match:
            try:
                presupuesto_clp = int(num_match.group(1).replace('.', ''))
            except (ValueError, TypeError):
                presupuesto_clp = None

        # 5. Obtención de productos reales de SoloTodo
        terminos_limpios = " ".join([w for w in re.findall(r'\b[a-zA-Z0-9áéíóúñ]{3,}\b', request.mensaje.lower()) if w not in {"hola", "busco", "necesito", "quiero", "cual", "que", "para", "con", "por", "menos", "mas", "recomiendas"}])
        query_busqueda = f"{carrera_detectada or ''} {terminos_limpios}".strip()

        productos_rel = buscar_productos(
            categoria=categoria,
            presupuesto_maximo=presupuesto_clp,
            query=query_busqueda,
            limite=4
        )
        if not productos_rel:
            productos_rel = buscar_productos(categoria=categoria, limite=4)

        # Perfil y requerimientos de la carrera
        perfil_carrera = PERFILES_CARRERAS.get(carrera_detectada) if carrera_detectada else None

        # Construir contexto de grounding
        contexto_prods = f"CATÁLOGO DE PRODUCTOS EN CHILE (SoloTodo - Categoría: {categoria.upper()}):\n"
        for p in productos_rel:
            contexto_prods += (
                f"- Modelo: {p.get('nombre')} | Precio referencial: {p.get('precio_clp')} | "
                f"Specs: {json.dumps(p.get('specs', {}))} | Enlace: {p.get('solotodo_url')}\n"
            )
        
        if perfil_carrera:
            contexto_prods += (
                f"\nESTÁNDAR ACADÉMICO UDEC:\n"
                f"- RAM mínima recomendada: {perfil_carrera.get('min_ram', 8)}GB\n"
                f"- GPU dedicada: {'Requerida' if perfil_carrera.get('gpu_dedicada') else 'Opcional / Integrada suficiente'}\n"
                f"- Justificación académica: {perfil_carrera.get('motivo')}\n"
            )

        # 6. System instruction institucional formal sin emojis, con límites estrictos de legalidad y temática
        system_instruction = (
            "Eres UdeskFit UdeC, asesor institucional inteligente de tecnología y equipamiento universitario "
            "de la Universidad de Concepción (iniciativa desarrollada por el laboratorio GIIA).\n"
            "NORMAS INSTITUCIONALES OBLIGATORIAS:\n"
            "1. Tu nombre oficial es UdeskFit UdeC. NUNCA te presentes ni te refieras a ti mismo como TechAdvisor.\n"
            "2. El usuario que consulta es un estudiante, docente o postulante general de cualquier carrera de la Universidad de Concepción. "
            "NO asumas que quien te consulta pertenece al GIIA ni lo trates como integrante de dicho grupo.\n"
            "3. NO utilices ningún emoji ni emoticón bajo ninguna circunstancia. Tu comunicación debe ser siempre formal, sobria, técnica y académica.\n"
            "4. Atiende consultas exclusivamente sobre computadores, notebooks, tablets, monitores, periféricos, software académico y calculadoras para ramos de la universidad.\n"
            "Si el usuario pregunta sobre cualquier tema ajeno (cocina, deportes, política, poemas, tareas generales, chistes, etc.), declina respetuosamente indicando: "
            "'Como asesor institucional de UdeskFit UdeC, solo puedo responder consultas sobre equipamiento tecnológico y requerimientos para la Universidad de Concepción.'\n"
            "5. NUNCA respondas ni asistas en actividades ilegales, armas, violencia, vulneración de sistemas, malware, piratería o cualquier acción dañina o dudosa.\n"
            "6. En tus recomendaciones, menciona modelos específicos disponibles en el catálogo, sus especificaciones técnicas destacadas, su valor referencial en CLP y el enlace a SoloTodo para que el estudiante revise tiendas en Chile.\n"
            "7. Sé directo, claro y conciso para optimizar la respuesta."
        )

        prompt_completo = (
            f"INFORMACIÓN VERIFICADA Y ACTUALIZADA DISPONIBLE EN EL SISTEMA:\n"
            f"{contexto_prods}\n\n"
            f"CONSULTA DEL ESTUDIANTE:\n"
            f"{request.mensaje}"
        )

        # Configuración de seguridad oficial Gemini (bloqueo de contenido dañino)
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
        ]

        # Configurar historial para multi-turno (ventana deslizante de ahorro de tokens)
        gemini_history = []
        for item in historial_previo:
            gemini_history.append(
                types.Content(
                    role=item["role"],
                    parts=[types.Part.from_text(text=item["text"])]
                )
            )

        modelos_candidatos = [
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
            "gemini-3.7-flash",
            "gemini-3.6-flash"
        ]
        
        respuesta_texto = None
        ultimo_error = None

        for modelo in modelos_candidatos:
            try:
                chat_session = client.chats.create(
                    model=modelo,
                    history=gemini_history,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.25,
                        max_output_tokens=700,
                        safety_settings=safety_settings
                    )
                )
                response = chat_session.send_message(prompt_completo)
                
                # Extraer texto de la respuesta
                if response and response.text:
                    respuesta_texto = response.text.strip()
                elif response and response.candidates:
                    cand = response.candidates[0]
                    if cand.content and cand.content.parts:
                        parts = [p.text for p in cand.content.parts if getattr(p, "text", None)]
                        if parts:
                            respuesta_texto = "".join(parts).strip()
                
                if respuesta_texto:
                    break
            except Exception as err:
                ultimo_error = err
                continue

        # Si ningún modelo respondió, utilizar recomendador estructurado local
        if not respuesta_texto:
            lineas_resp = [
                f"Estimado estudiante, en base a los requerimientos institucionales de la Universidad de Concepción para la categoría de {categoria}:",
                ""
            ]
            if perfil_carrera:
                lineas_resp.append(f"Criterio académico: {perfil_carrera.get('motivo')} (Mínimo recomendado: {perfil_carrera.get('min_ram', 8)}GB RAM).")
                lineas_resp.append("")
            
            lineas_resp.append("Opciones destacadas en el mercado nacional (SoloTodo):")
            for p in productos_rel[:3]:
                lineas_resp.append(f"- {p.get('nombre')}: {p.get('precio_clp')}. Enlace de tiendas: {p.get('solotodo_url')}")
            
            lineas_resp.append("")
            lineas_resp.append("Para más detalles o contrastar alternativas, puede explorar las pestañas de cotización superior.")
            respuesta_texto = "\n".join(lineas_resp)

        # Guardar en memoria de sesión
        session_manager.add_interaction(request.session_id, request.mensaje, respuesta_texto)
        return {"respuesta": respuesta_texto}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
