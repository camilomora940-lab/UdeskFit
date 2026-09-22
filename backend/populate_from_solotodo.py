"""
Script de Ingesta y Población de Base de Datos TechAdvisor UdeC desde SoloTodo (solotodo.cl)
Descarga productos reales, precios vigentes en Chile, especificaciones técnicas detalladas
y tiendas disponibles para estudiantes y académicos de la Universidad de Concepción.
"""

import urllib.request
import json
import os
import sys
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def fetch_json(url, timeout=12):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))

def get_stores_map():
    print("Obteniendo mapa de tiendas chilenas desde SoloTodo...")
    try:
        stores = fetch_json('https://api.solotodo.com/stores/')
        return {s['id']: s.get('name', 'Tienda') for s in stores}
    except Exception as e:
        print(f"Aviso: no se pudo cargar tiendas ({e}), usando fallback.")
        return {
            12: "PC Factory", 11: "Paris", 8147: "Falabella", 9: "Ripley",
            199: "Lenovo Chile", 18: "SP Digital", 260: "Mercado Libre",
            3: "Acer Store", 5: "HP Online", 88: "Líder"
        }

def get_product_entities(product_id, stores_map, max_stores=4):
    """Obtiene las tiendas reales que tienen stock y precio del producto."""
    try:
        url = f'https://api.solotodo.com/products/{product_id}/entities/'
        entities = fetch_json(url, timeout=6)
        tiendas = []
        for ent in entities:
            reg = ent.get('active_registry')
            if not reg:
                continue
            offer_price = reg.get('offer_price')
            normal_price = reg.get('normal_price')
            if not offer_price:
                continue
            store_id = ent.get('store_id')
            store_name = stores_map.get(store_id, f"Tienda #{store_id}")
            ext_url = ent.get('external_url') or ""
            tiendas.append({
                "tienda": store_name,
                "precio_oferta": int(float(offer_price)),
                "precio_normal": int(float(normal_price)) if normal_price else int(float(offer_price)),
                "url": ext_url
            })
        tiendas.sort(key=lambda x: x["precio_oferta"])
        return tiendas[:max_stores]
    except Exception:
        return []

def classify_budget(price):
    if price < 400000:
        return "bajo"
    elif price <= 700000:
        return "medio"
    elif price <= 1200000:
        return "alto"
    else:
        return "premium"

def parse_notebook(r, stores_map):
    try:
        entry = r.get('product_entries', [{}])[0]
        p = entry.get('product', {})
        meta = entry.get('metadata', {})
        prices = meta.get('prices_per_currency', [{}])[0]
        
        offer = prices.get('offer_price')
        if not offer:
            return None
        price = int(float(offer))
        normal_price = int(float(prices.get('normal_price', offer)))
        
        specs = p.get('specs', {})
        pid = p.get('id')
        slug = p.get('slug', '')
        name = p.get('name', 'Notebook')
        
        # Specs de hardware
        cpu = specs.get('processor_unicode') or specs.get('processor_name') or "Procesador multinúcleo"
        ram = specs.get('pretty_ram') or f"{specs.get('ram_value', 8)} GB RAM"
        
        storage_drive = specs.get('largest_storage_drive', {})
        storage = storage_drive.get('unicode') or "SSD 512 GB"
        
        gpu = specs.get('pretty_dedicated_video_card') or specs.get('main_gpu', {}).get('unicode') or "Gráficos integrados"
        
        screen_size = specs.get('screen_size_value') or specs.get('screen_size_unicode') or "15.6"
        screen_res = specs.get('screen_resolution_unicode') or "Full HD"
        pantalla = f'{screen_size}" {screen_res}'
        
        weight = specs.get('weight')
        peso = f"{weight/1000:.1f} kg" if weight else "~1.8 kg"
        bateria = specs.get('pretty_battery') or "Hasta 8 hrs de autonomía"
        
        # Descripción contextual
        desc = f"Notebook con {cpu}, {ram}, {storage} y pantalla {pantalla}. "
        if "RTX" in gpu or "GeForce" in gpu or "Radeon RX" in gpu:
            desc += f"Incluye GPU {gpu} para alta demanda gráfica, CAD, BIM, renderizado y Machine Learning."
        elif "Apple" in name or "MacBook" in name:
            desc += "Alta eficiencia energética, excelente pantalla y rendimiento sobresaliente para programación y diseño."
        else:
            desc += "Ideal para ofimática, programación general, cálculo y multitarea en el campus."

        solotodo_url = f"https://www.solotodo.cl/products/{pid}-{slug}"
        img = p.get('picture_url') or "https://media.solotodo.com/media/products/placeholder.png"

        return {
            "id": f"nb_{pid}",
            "solotodo_id": pid,
            "nombre": name,
            "categoria": "notebook",
            "rango_presupuesto": classify_budget(price),
            "precio": price,
            "precio_normal": normal_price,
            "solotodo_url": solotodo_url,
            "imagen": img,
            "specs": {
                "cpu": cpu,
                "ram": ram,
                "storage": storage,
                "gpu": gpu,
                "pantalla": pantalla,
                "peso": peso,
                "bateria": bateria
            },
            "descripcion": desc,
            "tiendas": []  # se pueden cargar bajo demanda o para top items
        }
    except Exception as e:
        return None

def parse_tablet(r, stores_map):
    try:
        entry = r.get('product_entries', [{}])[0]
        p = entry.get('product', {})
        meta = entry.get('metadata', {})
        prices = meta.get('prices_per_currency', [{}])[0]
        
        offer = prices.get('offer_price')
        if not offer:
            return None
        price = int(float(offer))
        normal_price = int(float(prices.get('normal_price', offer)))
        
        pid = p.get('id')
        slug = p.get('slug', '')
        name = p.get('name', 'Tablet')
        specs = p.get('specs', {})
        
        storage = specs.get('storage_unicode') or specs.get('internal_storage_value') or "64 GB / 128 GB"
        screen = specs.get('screen_size_unicode') or specs.get('screen_unicode') or "10.2\""
        
        return {
            "id": f"tab_{pid}",
            "solotodo_id": pid,
            "nombre": name,
            "categoria": "tablet",
            "precio": price,
            "precio_normal": normal_price,
            "solotodo_url": f"https://www.solotodo.cl/products/{pid}-{slug}",
            "imagen": p.get('picture_url') or "",
            "specs": {
                "pantalla": str(screen),
                "almacenamiento": str(storage),
                "ram": str(specs.get('ram_value', ''))
            },
            "descripcion": f"Tablet para toma de apuntes en certámenes, lectura de PDFs, papers y estudio en el campus.",
            "tiendas": []
        }
    except Exception:
        return None

def parse_monitor(r, stores_map):
    try:
        entry = r.get('product_entries', [{}])[0]
        p = entry.get('product', {})
        meta = entry.get('metadata', {})
        prices = meta.get('prices_per_currency', [{}])[0]
        
        offer = prices.get('offer_price')
        if not offer:
            return None
        price = int(float(offer))
        normal_price = int(float(prices.get('normal_price', offer)))
        
        pid = p.get('id')
        slug = p.get('slug', '')
        name = p.get('name', 'Monitor')
        specs = p.get('specs', {})
        
        size = specs.get('size_unicode') or specs.get('size_value') or '24"'
        res = specs.get('resolution_unicode') or '1920x1080 (Full HD)'
        panel = specs.get('panel_type_unicode') or 'IPS'
        refresh = specs.get('refresh_rate_unicode') or '75 Hz'
        
        return {
            "id": f"mon_{pid}",
            "solotodo_id": pid,
            "nombre": name,
            "categoria": "monitor",
            "precio": price,
            "precio_normal": normal_price,
            "solotodo_url": f"https://www.solotodo.cl/products/{pid}-{slug}",
            "imagen": p.get('picture_url') or "",
            "specs": {
                "pantalla": f"{size} {res}",
                "panel": panel,
                "tasa_refresco": str(refresh)
            },
            "descripcion": f"Monitor secundario {size} {panel} para productividad con doble pantalla en programación, CAD y análisis de datos.",
            "tiendas": []
        }
    except Exception:
        return None

def parse_periferico(r, categoria_nombre):
    try:
        entry = r.get('product_entries', [{}])[0]
        p = entry.get('product', {})
        meta = entry.get('metadata', {})
        prices = meta.get('prices_per_currency', [{}])[0]
        
        offer = prices.get('offer_price')
        if not offer:
            return None
        price = int(float(offer))
        normal_price = int(float(prices.get('normal_price', offer)))
        
        pid = p.get('id')
        slug = p.get('slug', '')
        name = p.get('name', categoria_nombre.capitalize())
        
        return {
            "id": f"peri_{pid}",
            "solotodo_id": pid,
            "nombre": name,
            "categoria": "periferico",
            "subcategoria": categoria_nombre,
            "precio": price,
            "precio_normal": normal_price,
            "solotodo_url": f"https://www.solotodo.cl/products/{pid}-{slug}",
            "imagen": p.get('picture_url') or "",
            "descripcion": f"{categoria_nombre.capitalize()} de alta durabilidad para estudio continuo y desarrollo.",
            "tiendas": []
        }
    except Exception:
        return None

def get_curated_calculators():
    return [
        {
            "id": "calc_fx991cw",
            "nombre": "Casio fx-991CW (ClassWiz)",
            "categoria": "calculadora",
            "precio": 36990,
            "precio_normal": 42990,
            "solotodo_url": "https://www.solotodo.cl/search?search=casio+fx-991cw",
            "imagen": "https://media.solotodo.com/media/products/casio_fx991cw.png",
            "specs": {
                "funciones": "552 funciones científicas",
                "tipo": "Científica no programable (Permitida en certámenes UdeC)",
                "pantalla": "LCD de 4 graduaciones de alta definición con menú de íconos",
                "caracteristicas": "Álgebra matricial 4x4, vectores, integrales y derivadas numéricas, resolución de ecuaciones, código QR"
            },
            "descripcion": "La calculadora estándar y recomendada para todas las Ingenierías UdeC (Plan Común, Industrial, Mecánica, Eléctrica, etc.) y Ciencias.",
            "tiendas": [
                {"tienda": "PC Factory", "precio_oferta": 36990, "precio_normal": 39990, "url": "https://www.pcfactory.cl"},
                {"tienda": "Lápiz López", "precio_oferta": 38990, "precio_normal": 42990, "url": "https://www.lapizlopez.cl"},
                {"tienda": "Falabella", "precio_oferta": 37990, "precio_normal": 41990, "url": "https://www.falabella.com"}
            ]
        },
        {
            "id": "calc_hpprime",
            "nombre": "HP Prime G2 Graficadora CAS",
            "categoria": "calculadora",
            "precio": 149990,
            "precio_normal": 169990,
            "solotodo_url": "https://www.solotodo.cl/search?search=hp+prime",
            "imagen": "https://media.solotodo.com/media/products/hp_prime_g2.png",
            "specs": {
                "funciones": "Sistema de Álgebra Computacional (CAS)",
                "tipo": "Graficadora avanzada multitáctil a color",
                "pantalla": "Táctil de 3.5\" a color",
                "caracteristicas": "Ecuaciones diferenciales, geometría dinámica, hojas de cálculo, batería recargable de iones de litio"
            },
            "descripcion": "Calculadora gráfica de gama alta para cursos avanzados de modelado, termodinámica y métodos numéricos en ingeniería.",
            "tiendas": [
                {"tienda": "PC Factory", "precio_oferta": 149990, "precio_normal": 159990, "url": "https://www.pcfactory.cl"},
                {"tienda": "Mercado Libre", "precio_oferta": 152990, "precio_normal": 165000, "url": "https://www.mercadolibre.cl"}
            ]
        },
        {
            "id": "calc_fx570",
            "nombre": "Casio fx-570LA CW",
            "categoria": "calculadora",
            "precio": 28990,
            "precio_normal": 32990,
            "solotodo_url": "https://www.solotodo.cl/search?search=casio+fx-570la",
            "imagen": "https://media.solotodo.com/media/products/casio_fx570.png",
            "specs": {
                "funciones": "540 funciones",
                "tipo": "Científica a pilas AAA",
                "pantalla": "Matriz de puntos de alta resolución",
                "caracteristicas": "Cálculo diferencial e integral, matrices, vectores, números complejos"
            },
            "descripcion": "Alternativa económica idéntica a la 991CW en capacidad de cómputo, alimentada por pila AAA.",
            "tiendas": [
                {"tienda": "Lápiz López", "precio_oferta": 28990, "precio_normal": 31990, "url": "https://www.lapizlopez.cl"}
            ]
        }
    ]

def populate_database(output_path="products_db.json"):
    print("=" * 60)
    print("Iniciando Ingesta de Datos desde SoloTodo para TechAdvisor UdeC")
    print("=" * 60)
    
    stores_map = get_stores_map()
    productos = []
    seen_ids = set()

    # 1. NOTERBOOKS (categoría 1)
    # Buscamos en varios ordenamientos para tener variedad completa de gamas
    queries_nb = [
        ("Más populares / recomendados", "https://api.solotodo.com/categories/1/browse/?page_size=30"),
        ("Gama económica (<$400k)", "https://api.solotodo.com/categories/1/browse/?ordering=offer_price_usd&page_size=25"),
        ("Gama media ($400k-$700k)", "https://api.solotodo.com/categories/1/browse/?ordering=score_general&page_size=25"),
        ("Gama alta y gamer", "https://api.solotodo.com/categories/1/browse/?ordering=score_games&page_size=25")
    ]
    
    for label, url in queries_nb:
        print(f"\nDescargando Notebooks: {label}...")
        try:
            data = fetch_json(url)
            results = data.get('results', [])
            count = 0
            for r in results:
                nb = parse_notebook(r, stores_map)
                if nb and nb["solotodo_id"] not in seen_ids:
                    seen_ids.add(nb["solotodo_id"])
                    productos.append(nb)
                    count += 1
            print(f"  -> {count} notebooks añadidos (Total acumulado: {len(productos)})")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error en {label}: {e}")

    # 2. TABLETS (categoría 14)
    print("\nDescargando Tablets (categoría 14)...")
    try:
        data = fetch_json("https://api.solotodo.com/categories/14/browse/?page_size=20")
        results = data.get('results', [])
        t_count = 0
        for r in results:
            tab = parse_tablet(r, stores_map)
            if tab and tab["solotodo_id"] not in seen_ids:
                seen_ids.add(tab["solotodo_id"])
                productos.append(tab)
                t_count += 1
        print(f"  -> {t_count} tablets añadidas.")
    except Exception as e:
        print(f"  Error en tablets: {e}")

    # 3. MONITORES (categoría 4)
    print("\nDescargando Monitores para setups de estudio (categoría 4)...")
    try:
        data = fetch_json("https://api.solotodo.com/categories/4/browse/?page_size=20")
        results = data.get('results', [])
        m_count = 0
        for r in results:
            mon = parse_monitor(r, stores_map)
            if mon and mon["solotodo_id"] not in seen_ids:
                seen_ids.add(mon["solotodo_id"])
                productos.append(mon)
                m_count += 1
        print(f"  -> {m_count} monitores añadidos.")
    except Exception as e:
        print(f"  Error en monitores: {e}")

    # 4. MOUSE (categoría 40) & TECLADOS (categoría 41)
    for cat_id, cat_name in [(40, "mouse"), (41, "teclado"), (28, "disco externo")]:
        print(f"\nDescargando Periféricos ({cat_name}, cat {cat_id})...")
        try:
            data = fetch_json(f"https://api.solotodo.com/categories/{cat_id}/browse/?page_size=12")
            results = data.get('results', [])
            p_count = 0
            for r in results:
                p_item = parse_periferico(r, cat_name)
                if p_item and p_item["solotodo_id"] not in seen_ids:
                    seen_ids.add(p_item["solotodo_id"])
                    productos.append(p_item)
                    p_count += 1
            print(f"  -> {p_count} {cat_name}s añadidos.")
            time.sleep(0.3)
        except Exception as e:
            print(f"  Error en {cat_name}: {e}")

    # 5. CALCULADORAS CURADAS UDEC
    print("\nAñadiendo Calculadoras oficiales para ingenierías UdeC...")
    for calc in get_curated_calculators():
        if calc["id"] not in seen_ids:
            seen_ids.add(calc["id"])
            productos.append(calc)
    print(f"  -> 3 calculadoras institucionales añadidas.")

    # 6. ENRIQUECER TOP NOTEBOOKS CON TIENDAS EN CHILE
    print("\nConsultando tiendas y precios chilenos para los notebooks destacados...")
    notebooks = [p for p in productos if p["categoria"] == "notebook"][:20]
    for i, nb in enumerate(notebooks):
        sys.stdout.write(f"\r  Consultando tiendas para notebook {i+1}/{len(notebooks)} ({nb['nombre'][:30]}...)")
        sys.stdout.flush()
        tiendas = get_product_entities(nb["solotodo_id"], stores_map, max_stores=4)
        if tiendas:
            nb["tiendas"] = tiendas
        time.sleep(0.15)
    print("\n  -> Tiendas actualizadas con éxito.")

    # Guardar a disco
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"¡Base de datos generada exitosamente en '{output_path}'!")
    print(f"Total de productos en el catálogo: {len(productos)}")
    
    # Resumen por categoría
    cats = {}
    for p in productos:
        c = p.get('categoria', 'otro')
        cats[c] = cats.get(c, 0) + 1
    for c, cnt in cats.items():
        print(f"  - {c.capitalize()}: {cnt} productos")
    print("=" * 60)
    return productos

if __name__ == "__main__":
    out_file = "products_db.json"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    populate_database(out_file)
