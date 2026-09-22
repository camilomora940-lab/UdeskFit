import time
import re

# Patrones prohibidos para filtrado local (Costo 0 de API)
PATRONES_PROHIBIDOS = [
    # Armas, explosivos y violencia
    r"\bbomb[as]?\b",
    r"\bexplosiv[oa]s?\b",
    r"\bdinamita\b",
    r"\barmas?\b",
    r"\bpistola[s]?\b",
    r"\brifle[s]?\b",
    r"\bdisparar\b",
    r"\bmatar\b",
    r"\basesinar\b",
    r"\bsuicidi[oa]\b",
    r"\bterroris[mt][ao]\b",
    
    # Actividades ilegales y delitos
    r"\brobar\b",
    r"\bhurtar\b",
    r"\bestafar?\b",
    r"\bfraude\b",
    r"\bdrogas?\b",
    r"\bcoca[ií]na\b",
    r"\bnarc[oó]tico[s]?\b",
    r"\btr[aá]fico\b",
    r"\binfringir\b.*\bley\b",
    r"\bviolar\b.*\bley\b",
    r"\bcometer\b.*\bdelito\b",
    
    # Ciberdelincuencia maliciosa
    r"\bmalware\b",
    r"\bransomware\b",
    r"\bkeylogger\b",
    r"\bphishing\b",
    r"\bclonar\b.*\btarjeta\b",
    r"\bhackear\b.*\b(cuenta|banco|clave|tarjeta|wifi|sistema)\b",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATRONES_PROHIBIDOS]

# Longitud máxima por mensaje para evitar consumo excesivo de tokens (protección cuota gratuita)
MAX_MESSAGE_LENGTH = 500

# Límite de mensajes guardados por sesión (Ventana deslizante de memoria)
# 4 mensajes = 2 turnos (usuario + modelo + usuario + modelo)
MAX_HISTORY_TURNS = 4

# Tiempo de expiración de sesión inactiva (en segundos, ej. 30 minutos)
SESSION_TTL_SECONDS = 1800

# Control de velocidad por sesión: mínimo de segundos entre peticiones del mismo usuario
MIN_INTERVAL_SECONDS = 1.5


class SessionManager:
    def __init__(self):
        # session_id -> {"last_active": float, "history": list[dict]}
        self._sessions: dict[str, dict] = {}

    def _cleanup_old_sessions(self):
        now = time.time()
        expired_keys = [
            sid for sid, data in self._sessions.items()
            if now - data.get("last_active", 0) > SESSION_TTL_SECONDS
        ]
        for sid in expired_keys:
            del self._sessions[sid]

        # Si aún hay demasiadas sesiones (más de 100), descartar las más antiguas
        if len(self._sessions) > 100:
            sorted_sessions = sorted(self._sessions.items(), key=lambda item: item[1].get("last_active", 0))
            for sid, _ in sorted_sessions[:30]:
                self._sessions.pop(sid, None)

    def is_rate_limited(self, session_id: str) -> bool:
        """Verifica si el usuario está enviando mensajes demasiado rápido (antispam para cuota gratuita)."""
        now = time.time()
        if session_id in self._sessions:
            last_req = self._sessions[session_id].get("last_request", 0)
            if now - last_req < MIN_INTERVAL_SECONDS:
                return True
        return False

    def get_history(self, session_id: str) -> list[dict]:
        """Obtiene el historial reciente de la sesión respetando la ventana de memoria."""
        self._cleanup_old_sessions()
        session = self._sessions.get(session_id)
        if not session:
            return []
        return session.get("history", [])

    def add_interaction(self, session_id: str, user_text: str, model_text: str):
        """Guarda la interacción en la memoria acotada."""
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "history": [],
                "last_active": now,
                "last_request": now
            }
        
        session = self._sessions[session_id]
        session["last_active"] = now
        session["last_request"] = now
        
        # Agregar mensajes recortados
        session["history"].append({"role": "user", "text": user_text[:MAX_MESSAGE_LENGTH]})
        session["history"].append({"role": "model", "text": model_text})
        
        # Mantener solo los últimos MAX_HISTORY_TURNS mensajes
        if len(session["history"]) > MAX_HISTORY_TURNS:
            session["history"] = session["history"][-MAX_HISTORY_TURNS:]


# Instancia única del gestor de sesiones
session_manager = SessionManager()


def validar_mensaje(mensaje: str, session_id: str = "default") -> tuple[bool, str | None]:
    """
    Valida el mensaje antes de llamar a la API de Gemini:
    1. Verifica si excede la tasa de peticiones (antispam).
    2. Verifica longitud para proteger la cuota gratuita.
    3. Filtra contenido prohibido/violento/ilegal con costo $0.
    
    Retorna (es_valido, mensaje_error_si_no_es_valido).
    """
    texto = mensaje.strip()
    if not texto:
        return False, "Por favor, escribe una pregunta o consulta sobre tecnología."

    # 1. Antispam
    if session_manager.is_rate_limited(session_id):
        return False, "Por favor espera un segundo antes de enviar otra consulta."

    # 2. Control de longitud (evita inyección masiva de tokens)
    if len(texto) > MAX_MESSAGE_LENGTH:
        return False, f"Tu consulta es demasiado larga (máximo {MAX_MESSAGE_LENGTH} caracteres). Por favor, sé más conciso para cuidar los recursos."

    # 3. Filtro local de seguridad y legalidad
    for patron in _COMPILED_PATTERNS:
        if patron.search(texto):
            return False, (
                "Lo siento, como asistente de Recomendador Tech solo puedo orientarte en "
                "asesoría, cotización y dudas sobre equipos computacionales y tecnología. "
                "No respondo preguntas sobre armas, actividades ilegales o fuera de este ámbito."
            )

    return True, None
