import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "products_db.json")

def cargar_catalogo():
    """Carga los productos desde products_db.json generado desde SoloTodo."""
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                prods = json.load(f)
                if prods and isinstance(prods, list):
                    # Normalizar campo link para retrocompatibilidad
                    for p in prods:
                        if "link" not in p:
                            p["link"] = p.get("solotodo_url", "https://www.solotodo.cl")
                    return prods
        except Exception as e:
            print(f"Error cargando products_db.json: {e}")

    # Fallback si no existe el archivo aún
    return [
        {
            "id": "1",
            "nombre": "Lenovo IdeaPad Gaming 3",
            "categoria": "notebook",
            "precio": 700000,
            "descripcion": "Notebook gamer ideal para programación y simulaciones. Intel Core i5, 16GB RAM, RTX 3050.",
            "link": "https://www.solotodo.cl",
            "solotodo_url": "https://www.solotodo.cl",
            "specs": {"cpu": "Intel Core i5", "ram": "16 GB", "gpu": "RTX 3050", "storage": "SSD 512GB"}
        }
    ]

CATALOGO_PRODUCTOS = cargar_catalogo()

def recargar_catalogo():
    """Vuelve a leer el archivo products_db.json desde el disco."""
    global CATALOGO_PRODUCTOS
    CATALOGO_PRODUCTOS = cargar_catalogo()
    return len(CATALOGO_PRODUCTOS)

def normalizar_ram_gb(specs: dict) -> int:
    ram_str = specs.get("ram", "")
    for part in ram_str.split():
        if part.isdigit():
            return int(part)
    return 8

def tiene_gpu_dedicada(specs: dict) -> bool:
    gpu = specs.get("gpu", "").lower()
    if not gpu or gpu == "no posee" or "integrada" in gpu or "iris" in gpu or "intel uhd" in gpu or "radeon 610" in gpu:
        return False
    if "rtx" in gpu or "gtx" in gpu or "geforce" in gpu or "radeon rx" in gpu or "arc " in gpu:
        return True
    return False

def buscar_productos(categoria: str = None, presupuesto_maximo: int = None, query: str = None, limite: int = 50) -> list:
    """
    Busca productos en el catálogo SoloTodo basándose en categoría, presupuesto y palabras clave.
    """
    resultados = list(CATALOGO_PRODUCTOS)
    
    if categoria:
        cat = categoria.lower().strip()
        def match_cat(p):
            p_cat = p.get("categoria", "").lower()
            p_sub = p.get("subcategoria", "").lower()
            if cat in p_cat or p_cat in cat:
                return True
            if p_sub and (cat in p_sub or p_sub in cat):
                return True
            if ("laptop" in cat or "computador" in cat or "portatil" in cat or "gamer" in cat) and p_cat == "notebook":
                return True
            if "ipad" in cat and p_cat == "tablet":
                return True
            if ("pantalla" in cat or "display" in cat) and p_cat == "monitor":
                return True
            if ("mouse" in cat or "teclado" in cat or "disco" in cat) and p_cat == "periferico":
                return True
            if ("calculadora" in cat or "casio" in cat or "prime" in cat) and p_cat == "calculadora":
                return True
            return False

        resultados = [p for p in resultados if match_cat(p)]
    
    if presupuesto_maximo:
        try:
            p_max = int(presupuesto_maximo)
            resultados = [p for p in resultados if p.get("precio", 0) <= p_max]
        except (ValueError, TypeError):
            pass

    if query:
        # Excluir términos redundantes de categoría y conectores
        terminos_ignorar = {"notebook", "laptop", "tablet", "monitor", "calculadora", "periferico", "para", "con", "por", "de", "un", "una", "el", "la"}
        q_terms = [t.lower().strip() for t in query.split() if len(t.strip()) > 1 and t.lower().strip() not in terminos_ignorar]
        
        if q_terms:
            def score_query(p):
                p_text = f"{p.get('nombre', '')} {p.get('descripcion', '')} {json.dumps(p.get('specs', {}))}".lower()
                score = 0
                for term in q_terms:
                    if term in p_text:
                        score += 10
                    # Bonificación especial si coincide en nombre o specs
                    if term in p.get('nombre', '').lower():
                        score += 15
                return score

            con_score = []
            for p in resultados:
                sc = score_query(p)
                if sc > 0:
                    con_score.append((sc, p))

            if con_score:
                # Ordenar por score de relevancia descendente, luego por precio más cercano al presupuesto si hay presupuesto
                if presupuesto_maximo:
                    con_score.sort(key=lambda item: (-item[0], -item[1].get("precio", 0)))
                else:
                    con_score.sort(key=lambda item: (-item[0], item[1].get("precio", 99999999)))
                resultados = [item[1] for item in con_score]
            elif presupuesto_maximo:
                # Si no hubo match de términos pero hay presupuesto, ordenar por los mejores dentro del presupuesto
                resultados.sort(key=lambda x: -x.get("precio", 0))
            else:
                resultados.sort(key=lambda x: x.get("precio", 99999999))
        else:
            if presupuesto_maximo:
                resultados.sort(key=lambda x: -x.get("precio", 0))
            else:
                resultados.sort(key=lambda x: x.get("precio", 99999999))
    else:
        if presupuesto_maximo:
            resultados.sort(key=lambda x: -x.get("precio", 0))
        else:
            resultados.sort(key=lambda x: x.get("precio", 99999999))
    
    formateados = []
    for p in resultados[:limite]:
        tiendas_str = ""
        if p.get("tiendas"):
            t_list = [f"{t['tienda']} (${t['precio_oferta']:,} CLP)" for t in p["tiendas"][:3]]
            tiendas_str = " | Tiendas: " + ", ".join(t_list)

        precio_val = p.get("precio", 0)
        formateados.append({
            "id": p.get("id"),
            "solotodo_id": p.get("solotodo_id"),
            "nombre": p.get("nombre"),
            "categoria": p.get("categoria"),
            "subcategoria": p.get("subcategoria"),
            "rango_presupuesto": p.get("rango_presupuesto"),
            "precio": precio_val,
            "precio_normal": p.get("precio_normal", precio_val),
            "precio_clp": f"${precio_val:,} CLP".replace(",", "."),
            "imagen": p.get("imagen", "https://media.solotodo.com/media/products/placeholder.png"),
            "specs": p.get("specs", {}),
            "tiendas": p.get("tiendas", []),
            "descripcion": p.get("descripcion", "") + tiendas_str,
            "solotodo_url": p.get("solotodo_url") or p.get("link", "https://www.solotodo.cl"),
            "link_solotodo": p.get("solotodo_url") or p.get("link", "https://www.solotodo.cl")
        })

    return formateados


def _cargar_perfiles_carreras():
    modular_path = os.path.join(os.path.dirname(__file__), "carreras_udec_modular.json")
    if os.path.exists(modular_path):
        try:
            with open(modular_path, "r", encoding="utf-8") as f:
                mod = json.load(f)
            fams = mod.get("families", {})
            cars = mod.get("carreras", {})
            profs = {}
            for slug, c in cars.items():
                fam = fams.get(c.get("family"), fams.get("business_quant", {}))
                p = dict(fam.get("db_profile", {}))
                p["nombre"] = c.get("label", slug)
                p["campus"] = c.get("campus", "Campus Concepción")
                p["url"] = c.get("url", f"https://admision.udec.cl/{slug}/")
                profs[slug] = p
            if profs:
                return profs
        except Exception as e:
            print(f"Error cargando carreras_udec_modular.json: {e}")

    # Fallback básico si el archivo no existe
    return {
        "ing_civil_informatica": {
            "min_ram": 16, "gpu_dedicada": True,
            "palabras_clave": ["rtx", "ryzen 7", "core i7", "legion", "16 gb", "32 gb"],
            "motivo": "Recomendado para desarrollo de software, Docker y compilación.",
            "badge": "Dev & VMs Ready", "nombre": "Ingeniería Civil Informática", "campus": "Campus Concepción"
        },
        "ing_civil_industrial": {
            "min_ram": 16, "gpu_dedicada": False,
            "palabras_clave": ["ryzen 7", "core i7", "thinkbook", "aspire", "16 gb"],
            "motivo": "Fluidez óptima para simulación de procesos, RStudio y optimización.",
            "badge": "Optimización & Datos", "nombre": "Ingeniería Civil Industrial", "campus": "Campus Concepción"
        }
    }

PERFILES_CARRERAS = _cargar_perfiles_carreras()



def recomendar_por_carrera(carrera: str = None, presupuesto: str = None, categoria: str = None, query: str = None, limite: int = 50) -> list:
    """
    Empareja de manera inteligente los productos reales de SoloTodo con los requerimientos de la carrera UdeC
    y el presupuesto seleccionado.
    """
    perfil = PERFILES_CARRERAS.get(carrera or "ing_civil_industrial", PERFILES_CARRERAS["ing_civil_industrial"])
    
    # 1. Filtro base de categoría
    prods = list(CATALOGO_PRODUCTOS)
    if categoria and categoria.lower() != "todos":
        cat = categoria.lower().strip()
        prods = [p for p in prods if cat in p.get("categoria", "").lower() or cat in p.get("subcategoria", "").lower()]

    # 2. Filtro de presupuesto
    if presupuesto and presupuesto.lower() not in ["todos", "all", ""]:
        p_str = presupuesto.lower().strip()
        def match_presupuesto(p):
            precio = p.get("precio", 0)
            if p_str == "bajo":
                return precio <= 450000
            elif p_str == "medio":
                return 400000 <= precio <= 750000
            elif p_str == "alto":
                return 700000 <= precio <= 1250000
            elif p_str == "premium":
                return precio >= 1200000
            return True
        prods = [p for p in prods if match_presupuesto(p)]

    # 3. Búsqueda por texto si existe
    if query:
        q_terms = [t.lower().strip() for t in query.split() if len(t.strip()) > 1]
        def match_q(p):
            t = f"{p.get('nombre', '')} {p.get('descripcion', '')} {json.dumps(p.get('specs', {}))}".lower()
            return any(term in t for term in q_terms)
        prods = [p for p in prods if match_q(p)]

    # 4. Ponderar compatibilidad con la carrera
    scored = []
    for p in prods:
        score = 50
        specs = p.get("specs", {})
        nombre = p.get("nombre", "").lower()
        desc = p.get("descripcion", "").lower()
        p_cat = p.get("categoria", "")

        tags = []
        razon = perfil.get("motivo", "")

        if p_cat == "notebook":
            ram_gb = normalizar_ram_gb(specs)
            min_ram = perfil.get("min_ram", 8)
            has_gpu = tiene_gpu_dedicada(specs)

            # RAM score
            if ram_gb >= min_ram:
                score += 25
                if ram_gb >= 32:
                    tags.append("32 GB RAM")
            else:
                score -= 20
                if presupuesto == "bajo":
                    tags.append(f"{ram_gb}GB (actualizable a {min_ram}GB)")

            # GPU score
            if perfil.get("gpu_dedicada", False):
                if has_gpu:
                    score += 25
                    tags.append("GPU Dedicada")
                else:
                    score -= 30
            else:
                if has_gpu:
                    score += 10
                    tags.append("GPU Dedicada")

            # Palabras clave del perfil
            for kw in perfil.get("palabras_clave", []):
                if kw in nombre or kw in desc:
                    score += 8
                    break

            # Pantalla OLED / Alta fidelidad
            if "oled" in specs.get("pantalla", "").lower() or "oled" in nombre:
                score += 12
                tags.append("Pantalla OLED")

            badge = perfil.get("badge", "Recomendado")
        
        elif p_cat == "tablet":
            score = 65
            if "apple" in nombre or "ipad" in nombre:
                score += 20
                tags.append("Compatible Apple Pencil")
            badge = "Apuntes & Movilidad"
        
        elif p_cat == "monitor":
            score = 60
            if "ips" in desc or "100%" in desc or "75hz" in desc or "144hz" in desc:
                score += 15
            badge = "Espacio de Trabajo"
        
        elif p_cat == "calculadora":
            score = 70
            if "casio" in nombre or "fx-991" in nombre:
                score += 25
                tags.append("Permitida en Certámenes")
            badge = "Cálculo Avanzado"
        
        elif p_cat == "periferico":
            score = 55
            if "ergonomico" in desc or "mx master" in nombre or "móvil" in desc or "ssd" in nombre:
                score += 15
            badge = "Accesorio Productividad"
        else:
            badge = "Recomendado"

        precio_val = p.get("precio", 0)
        tiendas_str = ""
        if p.get("tiendas"):
            t_list = [f"{t['tienda']} (${t['precio_oferta']:,} CLP)" for t in p["tiendas"][:3]]
            tiendas_str = " | Tiendas: " + ", ".join(t_list)

        scored.append({
            "id": p.get("id"),
            "solotodo_id": p.get("solotodo_id"),
            "nombre": p.get("nombre"),
            "categoria": p.get("categoria"),
            "subcategoria": p.get("subcategoria"),
            "precio": precio_val,
            "precio_normal": p.get("precio_normal", precio_val),
            "precio_clp": f"${precio_val:,} CLP".replace(",", "."),
            "imagen": p.get("imagen", "https://media.solotodo.com/media/products/placeholder.png"),
            "specs": specs,
            "tiendas": p.get("tiendas", []),
            "solotodo_url": p.get("solotodo_url") or p.get("link", "https://www.solotodo.cl"),
            "link_solotodo": p.get("solotodo_url") or p.get("link", "https://www.solotodo.cl"),
            "descripcion": p.get("descripcion", "") + tiendas_str,
            "score": score,
            "badge": badge,
            "tags": tags,
            "motivo_carrera": razon
        })

    # Ordenar por afinidad/score descendente y luego por precio
    scored.sort(key=lambda x: (-x["score"], x["precio"]))
    return scored[:limite]

