[README.md](https://github.com/user-attachments/files/33112137/README.md)
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
├── render.yaml                     # Configuración de despliegue en Render
├── Dockerfile                      # Configuración de imagen Docker
└── Procfile                        # Comando de inicio compatible con plataformas PaaS
```

## Requisitos

- Python 3.11
- Git

## Ejecución local

Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone https://github.com/camilomora940-lab/UdeskFit.git
cd UdeskFit
```

Crea y activa un entorno virtual. En Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Instala las dependencias e inicia el servidor desde la raíz del repositorio:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Abre estas direcciones en el navegador:

- Aplicación: <http://127.0.0.1:8000/>
- Panel de administración: <http://127.0.0.1:8000/admin>
- Documentación interactiva de la API: <http://127.0.0.1:8000/docs>
- Estado del servicio: <http://127.0.0.1:8000/api/health>

Usa la URL servida por FastAPI en vez de abrir `recomendador.html` directamente como archivo, ya que la interfaz consulta los endpoints del backend.

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

El repositorio incluye `render.yaml` para configurar el servicio web en Render. También incluye un `Dockerfile` para construir una imagen de la aplicación. En ambos casos, el punto de entrada de FastAPI es `backend.main:app`.

## Licencia

Este repositorio no incluye un archivo de licencia. Consulta a los responsables del proyecto antes de reutilizar o redistribuir su código, datos o recursos gráficos.
