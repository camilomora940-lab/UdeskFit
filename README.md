# UDeskFit UdeC

Recomendador de equipamiento tecnológico para estudiantes de la Universidad de Concepción. Permite explorar productos por carrera, categoría y presupuesto, y entrega orientación considerando los requerimientos académicos de cada carrera.

## Funcionalidades

- Recomendaciones de notebooks y otros productos tecnológicos según carrera, categoría y presupuesto.
- Catálogo local de productos con precios, especificaciones y enlaces de referencia a SoloTodo.
- Perfiles para las 92 carreras de la UdeC, distribuidas en sus campus.
- Asistente de orientación con historial acotado por sesión y límites de uso.
- Interfaz web y API servidas desde la misma aplicación FastAPI.

Las recomendaciones y respuestas del asistente se generan localmente a partir del catálogo y los perfiles incluidos en el repositorio; el backend no requiere una clave de API de un proveedor de IA.

## Tecnologías

- Python 3.11
- FastAPI y Uvicorn
- Docker y Docker Compose
- HTML, CSS y JavaScript
- Datos locales en formato JSON

## Estructura del repositorio

```text
.
├── assets/                         # Logos e imágenes de la interfaz
├── backend/
│   ├── main.py                     # Aplicación FastAPI y endpoints
│   ├── db_mock.py                  # Búsqueda del catálogo y perfiles de carrera
│   ├── guardrails.py               # Validaciones y límites de uso del chat
│   ├── products_db.json            # Catálogo local de productos
│   ├── carreras_detalladas_92.json # Perfiles detallados de carreras UdeC
│   └── requirements.txt            # Dependencias del backend
├── admin.html                      # Panel de administración
├── recomendador.html               # Interfaz principal
├── requirements.txt                # Dependencias para ejecutar y desplegar
├── compose.yaml                    # Servicio Docker Compose
├── render.yaml                     # Configuración de despliegue en Render
├── Dockerfile                      # Imagen Docker de la aplicación
├── .dockerignore                   # Archivos excluidos de la imagen Docker
└── Procfile                        # Comando de inicio compatible con plataformas PaaS
```

## Requisitos

- Git
- Docker Desktop (Windows/macOS) o Docker Engine con el plugin Docker Compose (Linux)

## Ejecutar con Docker Compose

Clona el repositorio y entra en la carpeta:

```bash
git clone https://github.com/camilomora940-lab/UdeskFit.git
cd UdeskFit
```

Desde la raíz del proyecto, inicia la aplicación:

```bash
docker compose up -d
```

Compose construye la imagen si es necesario e inicia el contenedor en segundo plano. Luego abre:

- Aplicación: <http://localhost:8000/>
- Panel de administración: <http://localhost:8000/admin>
- Documentación de la API: <http://localhost:8000/docs>
- Estado del servicio: <http://localhost:8000/api/health>

Para ver los registros:

```bash
docker compose logs -f
```

Para detener el servicio:

```bash
docker compose down
```

Al cambiar el código o las dependencias, reconstruye y reinicia con `docker compose up -d --build`.

### Variables de entorno

No se necesitan claves ni variables de entorno para ejecutar la configuración predeterminada. `APP_PORT` es opcional y cambia el puerto publicado en el equipo anfitrión; el puerto interno del contenedor permanece en `8000`.

Para usar un puerto distinto, crea un archivo `.env` en la raíz del repositorio:

```dotenv
APP_PORT=8080
```

Después inicia Compose con `docker compose up -d` y visita <http://localhost:8080/>. No agregues secretos al repositorio. El archivo `.dockerignore` excluye `.env` de la imagen.

### Ejecución sin Docker (opcional)

Se requiere Python 3.11. Instala las dependencias desde la raíz del repositorio y ejecuta FastAPI:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

La aplicación estará disponible en <http://127.0.0.1:8000/>. Usa la URL servida por FastAPI en vez de abrir `recomendador.html` directamente como archivo, ya que la interfaz consulta los endpoints del backend.

## API

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/health` | Estado de la aplicación y cantidad de productos |
| `GET` | `/api/carreras` | Lista de carreras y sus perfiles académicos |
| `GET` | `/api/productos` | Búsqueda del catálogo; admite filtros como `categoria`, `presupuesto_max`, `q` y `limit` |
| `GET` | `/api/recomendar` | Recomendaciones filtradas por carrera, categoría y presupuesto |
| `GET` | `/api/imagen-proxy` | Obtiene y cachea imágenes alojadas en SoloTodo |
| `POST` | `/api/chat` | Envía una consulta al asistente local |
| `POST` | `/api/chat/reset` | Reinicia el historial de una sesión |
| `POST` | `/api/admin/sync-solotodo` | Actualiza el catálogo local desde SoloTodo |

La documentación interactiva disponible en `/docs` muestra los parámetros y esquemas de cada endpoint.

## Datos del catálogo

El backend carga los productos desde `backend/products_db.json` al iniciar. Los perfiles de carrera se cargan desde `backend/carreras_detalladas_92.json`. La información de productos y precios puede cambiar; comprueba la disponibilidad y el precio vigente en el enlace de referencia antes de comprar.

## Despliegue

El repositorio incluye `render.yaml` para configurar el servicio web en Render y un `Dockerfile` para construir la imagen. El punto de entrada de FastAPI es `backend.main:app`.

## Licencia

Este repositorio no incluye un archivo de licencia. Consulta a los responsables del proyecto antes de reutilizar o redistribuir su código, datos o recursos gráficos.
