import os
import sys
import re
import json
import hashlib
import urllib.request
import hmac
from datetime import datetime, timedelta, timezone

# Asegurar que el directorio backend esté siempre en sys.path (para despliegue en Render, Railway, Docker)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from db_mock import buscar_productos, recargar_catalogo, CATALOGO_PRODUCTOS, recomendar_por_carrera, PERFILES_CARRERAS
from guardrails import validar_mensaje, session_manager

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

app = FastAPI(title="UDeskFit - Recomendador Tech UdeC API")
bearer_scheme = HTTPBearer(auto_error=False)
ADMIN_TOKEN_TTL_MINUTES = 30

# Rutas estáticas para despliegue unificado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=500)
    session_id: str = Field(min_length=1, max_length=128)
    session_token: str = Field(min_length=1, max_length=256)


class ChatSessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    session_token: str = Field(min_length=1, max_length=256)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


def get_admin_auth_config() -> tuple[str, str, str]:
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    secret = os.getenv("JWT_SECRET_KEY", "")
    if not username or not password or not secret:
        raise HTTPException(
            status_code=503,
            detail="La autenticación administrativa no está configurada.",
        )
    if len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=503,
            detail="JWT_SECRET_KEY debe tener al menos 32 bytes.",
        )
    return username, password, secret


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Se requiere un token de administrador.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, _, secret = get_admin_auth_config()
    try:
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "role"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("role") != "admin" or payload.get("sub") != username:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para esta operación.",
        )
    return username


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

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "UDeskFit UdeC",
        "productos_en_catalogo": len(CATALOGO_PRODUCTOS),
        "ai_status": "local_only"
    }


@app.post("/api/auth/login")
def admin_login(request: AdminLoginRequest):
    username, password, secret = get_admin_auth_config()
    valid_username = hmac.compare_digest(
        request.username.strip().encode("utf-8"),
        username.encode("utf-8"),
    )
    valid_password = hmac.compare_digest(
        request.password.encode("utf-8"),
        password.encode("utf-8"),
    )
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ADMIN_TOKEN_TTL_MINUTES)
    token = jwt.encode(
        {
            "sub": username,
            "role": "admin",
            "iat": now,
            "exp": expires_at,
        },
        secret,
        algorithm="HS256",
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ADMIN_TOKEN_TTL_MINUTES * 60,
        "role": "admin",
    }


CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache_images")
os.makedirs(CACHE_DIR, exist_ok=True)

# Límites del proxy de imágenes (Hallazgo I)
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB máximo por imagen
MAX_CACHE_FILES = 500  # Máximo de imágenes en caché


def _enforce_cache_limit():
    """Elimina los archivos más antiguos del caché si se excede MAX_CACHE_FILES."""
    try:
        cache_files = [
            os.path.join(CACHE_DIR, f)
            for f in os.listdir(CACHE_DIR)
            if not f.endswith(".meta")
        ]
        if len(cache_files) <= MAX_CACHE_FILES:
            return
        # Ordenar por mtime (más antiguo primero) y eliminar excedentes
        cache_files.sort(key=lambda p: os.path.getmtime(p))
        for path in cache_files[: len(cache_files) - MAX_CACHE_FILES]:
            try:
                os.remove(path)
                meta = path + ".meta"
                if os.path.exists(meta):
                    os.remove(meta)
            except OSError:
                pass
    except OSError:
        pass

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
def imagen_proxy(url: str = Query(max_length=2048)):
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
            # Leer con límite de tamaño para evitar uso descontrolado de RAM
            data = resp.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"La imagen excede el tamaño máximo permitido ({MAX_IMAGE_BYTES // (1024 * 1024)} MB)."
                )
            mime_type = detect_mime(data, url)
            
            # Guardar en caché respetando el límite de archivos
            try:
                _enforce_cache_limit()
                with open(cache_path, 'wb') as f:
                    f.write(data)
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(mime_type)
            except Exception:
                pass
                
            return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=2592000"})
    except urllib.error.HTTPError as he:
        raise HTTPException(status_code=he.code, detail=f"SoloTodo devolvió error {he.code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error obteniendo imagen de SoloTodo: {str(e)}")

@app.get("/api/productos")
def listar_productos(
    categoria: str = Query(default=None, max_length=64),
    presupuesto_max: int = Query(default=None, ge=0, le=100_000_000),
    q: str = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Retorna productos del catálogo SoloTodo filtrados por categoría, presupuesto y búsqueda."""
    res = buscar_productos(categoria=categoria, presupuesto_maximo=presupuesto_max, query=q, limite=limit)
    return {
        "status": "ok",
        "total_en_catalogo": len(CATALOGO_PRODUCTOS),
        "total_encontrados": len(res),
        "productos": res
    }

@app.get("/api/recomendar")
def api_recomendar(
    carrera: str = Query(default="ing_civil_industrial", max_length=128),
    presupuesto: str = Query(default=None, max_length=20),
    categoria: str = Query(default=None, max_length=64),
    q: str = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
):
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
def sync_solotodo(_: str = Depends(require_admin)):
    """Ejecuta la actualización del catálogo desde SoloTodo."""
    try:
        from populate_from_solotodo import populate_database
        db_file = os.path.join(os.path.dirname(__file__), "products_db.json")
        populate_database(db_file)
        total = recargar_catalogo()
        return {"status": "ok", "message": f"Catálogo sincronizado exitosamente con SoloTodo ({total} productos actualizados)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando con SoloTodo: {str(e)}")

@app.post("/api/chat/session")
def create_chat_session(http_request: Request):
    """Issues an opaque session reference and a token required to use it."""
    if http_request.client is None or not http_request.client.host:
        raise HTTPException(status_code=503, detail="No se pudo determinar el origen de la conexión.")
    try:
        session_id, session_token = session_manager.create_session(http_request.client.host)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    return {"session_id": session_id, "session_token": session_token}


@app.post("/api/chat/reset")
def reset_session(request: ChatSessionRequest):
    """Permite reiniciar el historial de una conversación."""
    if not session_manager.delete_session(request.session_id, request.session_token):
        raise HTTPException(status_code=404, detail="Sesión no encontrada o credenciales inválidas.")
    return {"status": "ok", "message": "Historial reiniciado correctamente."}

@app.post("/api/chat")
def chat(chat_request: ChatRequest, http_request: Request):
    if not session_manager.verify_session(chat_request.session_id, chat_request.session_token):
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada.")

    if http_request.client is None or not http_request.client.host:
        raise HTTPException(status_code=503, detail="No se pudo determinar el origen de la conexión.")

    # 1. Filtro local de seguridad y optimización de cuota (Costo $0)
    es_valido, error_guardrail = validar_mensaje(
        chat_request.mensaje,
        http_request.client.host,
    )
    if not es_valido:
        return {"respuesta": error_guardrail}

    try:
        msg_lower = chat_request.mensaje.lower()
        historial_previo = session_manager.get_history(chat_request.session_id)
        
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
        num_match = re.search(r'(\d{1,3}(?:\.\d{3})+|\d{5,8})', chat_request.mensaje.replace('$', ''))
        if num_match:
            try:
                presupuesto_clp = int(num_match.group(1).replace('.', ''))
            except (ValueError, TypeError):
                presupuesto_clp = None

        # 5. Obtención de productos reales de SoloTodo
        terminos_limpios = " ".join([w for w in re.findall(r'\b[a-zA-Z0-9áéíóúñ]{3,}\b', chat_request.mensaje.lower()) if w not in {"hola", "busco", "necesito", "quiero", "cual", "que", "para", "con", "por", "menos", "mas", "recomiendas"}])
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

        temas_permitidos = [
            "tecnolog", "comput", "notebook", "laptop", "tablet", "calculadora",
            "monitor", "mouse", "teclado", "audifono", "perifer", "software",
            "program", "ram", "gpu", "memoria", "udec", "carrera", "estudi",
            "equipo", "pc", "mac", "windows", "linux", "presupuesto", "precio",
        ]
        consulta_permitida = carrera_detectada or any(term in msg_lower for term in temas_permitidos)

        if not consulta_permitida:
            respuesta_texto = (
                "Como asesor de UdeskFit UdeC, solo puedo orientar sobre equipamiento "
                "tecnológico y software académico para la Universidad de Concepción."
            )
        else:
            lineas_resp = [
                f"Recomendación local UdeskFit UdeC para {categoria}:",
                "",
            ]
            if perfil_carrera:
                lineas_resp.append(
                    f"Criterio académico para {perfil_carrera.get('nombre', 'la carrera')}: "
                    f"{perfil_carrera.get('motivo')} (mínimo recomendado: "
                    f"{perfil_carrera.get('min_ram', 8)} GB RAM)."
                )
                software = perfil_carrera.get("software", [])
                if software:
                    lineas_resp.append(f"Software de referencia: {', '.join(software[:5])}.")
                if perfil_carrera.get("alert"):
                    lineas_resp.append(f"Nota: {perfil_carrera['alert']}")
                lineas_resp.append("")

            if presupuesto_clp:
                lineas_resp.append(f"Presupuesto indicado: ${presupuesto_clp:,} CLP.".replace(",", "."))

            if productos_rel:
                lineas_resp.append("Opciones disponibles en el catálogo local:")
                for producto in productos_rel[:3]:
                    lineas_resp.append(
                        f"- {producto.get('nombre')}: {producto.get('precio_clp')}."
                    )
                    specs = producto.get("specs", {})
                    if isinstance(specs, dict):
                        specs_resumen = ", ".join(
                            f"{nombre.upper()}: {valor}"
                            for nombre, valor in list(specs.items())[:4]
                            if valor
                        )
                        if specs_resumen:
                            lineas_resp.append(f"  Especificaciones: {specs_resumen}.")
                    if producto.get("solotodo_url"):
                        lineas_resp.append(f"  Referencia: {producto['solotodo_url']}")
            else:
                lineas_resp.append(
                    "No encontré productos que coincidan en el catálogo local. "
                    "Prueba con otra categoría o presupuesto."
                )

            respuesta_texto = "\n".join(lineas_resp)

        # Guardar en memoria de sesión
        session_manager.add_interaction(chat_request.session_id, chat_request.mensaje, respuesta_texto)
        return {"respuesta": respuesta_texto}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
