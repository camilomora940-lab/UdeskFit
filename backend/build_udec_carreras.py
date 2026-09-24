"""
Generador del catálogo completo y oficial de 92 carreras UdeC
Extraído directamente de http://admision.udec.cl/carreras-udec/
"""
import json
import re

with open('carreras_udec_parsed.json', 'r', encoding='utf-8') as f:
    raw_carreras = json.load(f)

# Plantillas por familia disciplinar
FAMILIES = {
    "software_dev": {
        "scores": {"CPU": 9, "RAM": 9, "Storage": 8, "GPU": 6, "Battery": 6, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#22c55e", "Battery": "#f59e0b", "Display": "#14b8a6"},
        "alert": "<strong>Carrera de alta exigencia de cómputo:</strong> Requerirás compilar proyectos, ejecutar máquinas virtuales (VM), contenedores Docker y múltiples IDEs. Menos de 16GB de RAM se queda corto rápidamente.",
        "software": ["VS Code / IntelliJ", "Docker + VMs", "Git + GitHub", "Linux WSL2", "Python / C++ / Java"],
        "laptops": {
            "ideal": {
                "name": "ASUS ROG Zephyrus G14 / Lenovo Legion Slim 5",
                "cpu": "AMD Ryzen 9 / 7 serie 7000H o Intel Core i7-13700H",
                "ram": "32 GB DDR5",
                "storage": "SSD NVMe 1TB PCIe 4.0",
                "gpu": "NVIDIA RTX 4060 8GB GDDR6",
                "battery": "~6-8 hrs",
                "display": '14"-16" QHD 144Hz+',
                "price": "$1.100.000 – $1.600.000",
                "why": "32GB permiten correr 2 VMs + contenedores + IDEs sin cuello de botella. La GPU dedicada acelera modelos de Machine Learning y procesamiento paralelo."
            },
            "balance": {
                "name": "Lenovo IdeaPad Gaming 3 / HP Victus 15",
                "cpu": "AMD Ryzen 5 7535H o Intel Core i5-12500H",
                "ram": "16 GB DDR5 (con slot para expandir)",
                "storage": "SSD NVMe 512GB",
                "gpu": "NVIDIA RTX 3050 4GB/6GB",
                "battery": "~5-7 hrs",
                "display": '15.6" FHD IPS 144Hz',
                "price": "$650.000 – $900.000",
                "why": "Excelente relación costo/beneficio con GPU CUDA para primeros ramos de IA y compilar fluidamente. 16GB aseguran fluidez los primeros 3 años."
            },
            "eco": {
                "name": "Laptop Ryzen 5 serie 5000/7000 + upgrade a 16GB",
                "cpu": "AMD Ryzen 5 5500U/7530U o Intel i5 12va gen",
                "ram": "8 GB DDR4 (actualizar inmediatamente a 16GB)",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados Radeon / Iris Xe",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$380.000 – $520.000",
                "why": "Excelente base para programar y aprender algoritmos en los primeros semestres; la actualización a 16GB es indispensable."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "Tablet Samsung Galaxy Tab S9 FE / iPad 10ma", "reason": "Complemento opcional para lectura de PDFs y diagramación rápida, aunque la prioridad #1 es siempre la laptop.", "price": "$300.000 – $420.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "Calculadora científica recomendada para ramos matemáticos del plan común (Cálculo I-III y Álgebra).", "price": "~$32.000 – $42.000 CLP" }
        ],
        "accessories": [
            { "name": "Monitor externo 24-27\" IPS FHD/QHD", "priority": "rec", "reason": "Tener dos pantallas al programar duplica la productividad (código en una, consola/documentación en la otra)." },
            { "name": "Teclado mecánico y mouse ergonómico", "priority": "rec", "reason": "Evita fatiga muscular y síndrome del túnel carpiano por largas sesiones de código." },
            { "name": "Disco externo SSD NVMe 1TB", "priority": "must", "reason": "Respaldos periódicos de repositorios, máquinas virtuales y proyectos de titulación." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": True,
            "palabras_clave": ["rtx", "ryzen 7", "core i7", "legion", "tuf", "victus", "loq", "16 gb", "32 gb"],
            "motivo": "Recomendado para desarrollo de software, múltiples IDEs, Docker y compilación pesada.",
            "badge": "Dev & VMs Ready"
        }
    },

    "cad_heavy": {
        "scores": {"CPU": 8, "RAM": 8, "Storage": 8, "GPU": 8, "Battery": 6, "Display": 8},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#ef4444", "Battery": "#f59e0b", "Display": "#22c55e"},
        "alert": "<strong>Carrera de modelado 3D y simulación técnica:</strong> Se requiere GPU dedicada (NVIDIA GeForce RTX) y mínimo 16GB de RAM para software como AutoCAD, SolidWorks, Revit, Inventor o ANSYS sin colgarse en el viewport 3D.",
        "software": ["AutoCAD", "SolidWorks / Inventor", "Revit / BIM", "ANSYS / FEA", "MATLAB"],
        "laptops": {
            "ideal": {
                "name": "ASUS TUF Gaming / Lenovo LOQ / Legion",
                "cpu": "Intel Core i7-13650HX o AMD Ryzen 7 7840HS",
                "ram": "16 GB a 32 GB DDR5",
                "storage": "SSD NVMe 1TB PCIe 4.0",
                "gpu": "NVIDIA GeForce RTX 4060 8GB GDDR6",
                "battery": "~5-7 hrs",
                "display": '15.6" o 16" FHD/QHD 144Hz IPS 100% sRGB',
                "price": "$950.000 – $1.400.000",
                "why": "La GPU dedicada RTX acelera el renderizado por hardware y el cálculo por elementos finitos. 16GB+ garantizan fluidez con ensamblajes grandes."
            },
            "balance": {
                "name": "Acer Nitro V15 / Lenovo IdeaPad Gaming 3",
                "cpu": "AMD Ryzen 5 7535HS o Intel Core i5-13420H",
                "ram": "16 GB DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "NVIDIA RTX 3050 / RTX 4050",
                "battery": "~5-6 hrs",
                "display": '15.6" FHD 144Hz IPS',
                "price": "$650.000 – $850.000",
                "why": "Punto de equilibrio perfecto: tarjeta dedicada suficiente para modelado de piezas, planos BIM y proyectos de taller."
            },
            "eco": {
                "name": "Notebook Ryzen 5 / i5 con GPU GTX 1650 / RTX 2050 / 3050 refurbished",
                "cpu": "AMD Ryzen 5 5600H o Intel Core i5 11va gen",
                "ram": "8 GB → actualizar a 16GB",
                "storage": "SSD NVMe 512GB",
                "gpu": "NVIDIA GTX 1650 o RTX 3050",
                "battery": "~4-6 hrs",
                "display": '15.6" FHD',
                "price": "$420.000 – $580.000",
                "why": "Equipo con GPU dedicada de entrada que cumple los requerimientos mínimos de acreditación de software técnico."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "iPad 10ma gen con Apple Pencil", "reason": "Excelente para bosquejos iniciales a mano alzada, revisión de planos en terreno y anotaciones técnicas.", "price": "$330.000 – $420.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz — Recomendada", "why": "Cálculo vectorial, matricial y ecuaciones simultáneas para ramos de Mecánica, Estática y Dinámica.", "price": "~$32.000 – $42.000 CLP" },
            { "name": "HP Prime v2 / TI-Nspire CX II CAS", "why": "Graficadora avanzada para cálculo de vigas, deformaciones y optimización.", "price": "~$130.000 – $190.000 CLP" }
        ],
        "accessories": [
            { "name": "Mouse ergonómico con rueda de precisión (CAD)", "priority": "must", "reason": "El botón central (scroll) es vital para paneo y órbita 3D en AutoCAD y SolidWorks." },
            { "name": "Monitor externo 27\" QHD IPS", "priority": "rec", "reason": "Área de trabajo amplia para ver planos a escala y herramientas simultáneamente." },
            { "name": "Base refrigerante para laptop", "priority": "rec", "reason": "Mantiene temperaturas estables durante renders y simulaciones pesadas prolongadas." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": True,
            "palabras_clave": ["rtx", "tuf", "legion", "loq", "nitro", "victus", "ryzen 7", "core i7"],
            "motivo": "Recomendado para modelado 3D CAD, planos BIM, AutoCAD y cálculo de elementos finitos.",
            "badge": "CAD 3D & FEA"
        }
    },

    "electronics": {
        "scores": {"CPU": 8, "RAM": 8, "Storage": 7, "GPU": 4, "Battery": 7, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera de circuitos y simulación matemática:</strong> Se requiere buen procesador y 16GB de RAM para MATLAB/Simulink, diseño de PCBs en Altium/KiCad y simulación SPICE de circuitos analógicos y digitales.",
        "software": ["MATLAB / Simulink", "LTSpice / Proteus", "Altium Designer / KiCad", "Python / C++", "LabVIEW"],
        "laptops": {
            "ideal": {
                "name": "Lenovo ThinkBook 16 / ASUS VivoBook Pro",
                "cpu": "Intel Core i7-13700H o AMD Ryzen 7 7735HS",
                "ram": "16 GB a 32 GB DDR5",
                "storage": "SSD NVMe 1TB PCIe 4.0",
                "gpu": "NVIDIA RTX 3050 o Radeon 780M avanzada",
                "battery": "~8-10 hrs",
                "display": '15.6" o 16" FHD IPS mate',
                "price": "$800.000 – $1.100.000",
                "why": "Potencia multicore para simulaciones pesadas de circuitos en el dominio del tiempo y frecuencia sin demoras."
            },
            "balance": {
                "name": "Acer Aspire 5 / ASUS VivoBook 15",
                "cpu": "AMD Ryzen 7 7730U o Intel Core i5-1335U",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados Radeon / Iris Xe",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$520.000 – $720.000",
                "why": "Capacidad óptima para programar microcontroladores, ESP32, Arduino y correr simulaciones SPICE."
            },
            "eco": {
                "name": "Lenovo IdeaPad 3 / HP 15 Ryzen 5",
                "cpu": "AMD Ryzen 5 5500U o Intel Core i5 11va gen",
                "ram": "8 GB (ampliable a 16GB)",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-8 hrs",
                "display": '15.6" FHD',
                "price": "$360.000 – $480.000",
                "why": "Equipo accesible con buen procesador capaz de cubrir los ramos de circuitos y programación."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "iPad 10ma gen o Galaxy Tab S6 Lite", "reason": "Útil para dibujar diagramas esquemáticos rápidos, revisar datasheets de componentes y apuntes de clases.", "price": "$220.000 – $360.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "Esencial para números complejos (forma polar y rectangular), cálculo de fasores e impedancias en certámenes.", "price": "~$32.000 – $42.000 CLP" },
            { "name": "HP Prime v2", "why": "Graficadora con transformada de Laplace y Fourier simbólica para ramos de Control y Señales.", "price": "~$140.000 – $190.000 CLP" }
        ],
        "accessories": [
            { "name": "Hub USB multipuerto USB-A y USB-C", "priority": "must", "reason": "Para conectar placas de desarrollo (Arduino, STM32), osciloscopios USB y programadores PIC." },
            { "name": "Mouse ergonómico", "priority": "rec", "reason": "Precisión para ruteo de pistas en PCB sobre KiCad o Altium." },
            { "name": "Disco externo o pendrive rápido", "priority": "must", "reason": "Guardar librerías de componentes y proyectos de laboratorio." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["ryzen 7", "core i7", "thinkbook", "aspire", "vivobook", "16 gb"],
            "motivo": "Excelente procesador para simulaciones SPICE, MATLAB/Simulink y diseño de circuitos.",
            "badge": "Simulación & Circuitos"
        }
    },

    "process_eng": {
        "scores": {"CPU": 8, "RAM": 8, "Storage": 7, "GPU": 4, "Battery": 7, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera de ingeniería de procesos y ciencias aplicadas:</strong> Se requiere memoria RAM amplia (16GB) para software de simulación como Aspen HYSYS, modelación termodinámica, MATLAB y balances de masa/energía.",
        "software": ["Aspen HYSYS / Plus", "MATLAB", "AutoCAD P&ID", "RStudio", "Excel Solver avanzado"],
        "laptops": {
            "ideal": {
                "name": "Lenovo ThinkBook 16 / HP EliteBook 845",
                "cpu": "AMD Ryzen 7 7730U/7735HS o Intel Core i7-1355U",
                "ram": "16 GB a 32 GB DDR5",
                "storage": "SSD NVMe 1TB PCIe",
                "gpu": "Gráficos Radeon / Iris Xe integrados",
                "battery": "~9-11 hrs",
                "display": '15.6"-16" FHD IPS mate',
                "price": "$750.000 – $1.000.000",
                "why": "16GB a 32GB son ideales para correr simuladores de plantas químicas y reactores sin pérdida de datos."
            },
            "balance": {
                "name": "Acer Aspire 5 / ASUS VivoBook 15",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5-1235U/1335U",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$500.000 – $700.000",
                "why": "Estándar recomendado que corre Aspen y hojas de cálculo masivas con total estabilidad."
            },
            "eco": {
                "name": "Notebook Ryzen 5 / i5 + ampliación a 16GB",
                "cpu": "AMD Ryzen 5 5500U o Intel Core i5 10ma/11ma",
                "ram": "8 GB (ampliar a 16GB para ramos de 3er año)",
                "storage": "SSD NVMe 256GB/512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-8 hrs",
                "display": '15.6" FHD',
                "price": "$350.000 – $480.000",
                "why": "Económico para los dos primeros años de plan común, con margen de actualización."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "Tablet Samsung Galaxy Tab A9+ / iPad", "reason": "Para lectura de diagramas de flujo de procesos (PFD/P&ID) y guías de laboratorio.", "price": "$170.000 – $320.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "Permite resolver sistemas de ecuaciones no lineales y tablas termodinámicas en certámenes.", "price": "~$32.000 – $42.000 CLP" }
        ],
        "accessories": [
            { "name": "Mouse inalámbrico confiable", "priority": "must", "reason": "Indispensable para navegar hojas de cálculo kilométricas y diagramas de plantas." },
            { "name": "Monitor externo 24\" FHD", "priority": "rec", "reason": "Permite contrastar literatura técnica y simulaciones a la vez." },
            { "name": "Pendrive resistente o disco externo", "priority": "must", "reason": "Para transportar datos de experimentos de laboratorio de manera segura." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["ryzen 7", "core i7", "thinkbook", "aspire", "vivobook", "16 gb"],
            "motivo": "Capacidad de memoria para simulación de procesos químicos, modelado termodinámico y balances.",
            "badge": "Simulación de Procesos"
        }
    },

    "business_quant": {
        "scores": {"CPU": 7, "RAM": 8, "Storage": 7, "GPU": 3, "Battery": 8, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera de modelación, analítica y gestión:</strong> El software clave incluye Python, R, Power BI, Excel Solver y simuladores como Simio o Arena. 16GB de RAM evitan congelamientos al procesar datasets masivos.",
        "software": ["Python + Pandas", "R + RStudio", "Power BI / Tableau", "Excel avanzado + VBA", "Simio / Arena"],
        "laptops": {
            "ideal": {
                "name": "Lenovo ThinkBook 16 G6 / HP EliteBook 845",
                "cpu": "AMD Ryzen 7 7730U o Intel Core i7-1355U",
                "ram": "16 GB DDR4/DDR5 3200MHz+",
                "storage": "SSD NVMe 512GB / 1TB",
                "gpu": "Gráficos integrados Radeon / Iris Xe",
                "battery": "~10-12 hrs",
                "display": '15.6"-16" FHD IPS Anti-glare',
                "price": "$750.000 – $950.000",
                "why": "16GB indispensables para correr RStudio, Power BI y simuladores en paralelo. Gran teclado con pad numérico para ingreso de datos."
            },
            "balance": {
                "name": "ASUS VivoBook 15 / Acer Aspire 5",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5-1235U",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$500.000 – $700.000",
                "why": "Excelente equilibrio. Abre modelos de optimización y bases de datos en pocos segundos."
            },
            "eco": {
                "name": "Notebook refurbished i5/Ryzen 5 con SSD",
                "cpu": "Intel Core i5 10ma gen o AMD Ryzen 5 serie 4000",
                "ram": "8 GB (actualizable a 16GB)",
                "storage": "SSD 256GB / 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~6-8 hrs",
                "display": '15.6" FHD',
                "price": "$280.000 – $420.000",
                "why": "Opción económica eficiente; al sumar $30k en un segundo módulo de RAM queda como equipo de gama media."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "iPad 9a/10a gen o Galaxy Tab S9 FE", "reason": "Muy recomendada para lectura de papers, casos de estudio en grupos y presentaciones de negocios.", "price": "$240.000 – $390.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "552 funciones, álgebra matricial, estadística avanzada y distribuciones de probabilidad.", "price": "~$32.000 – $42.000 CLP" },
            { "name": "HP 12c Financiera (Opcional)", "why": "Clásica para ramos avanzados de Finanzas, flujos de caja y tasas de interés.", "price": "~$45.000 – $65.000 CLP" }
        ],
        "accessories": [
            { "name": "Mouse ergonómico inalámbrico con teclado numérico", "priority": "must", "reason": "Fundamental para jornadas largas con hojas de cálculo y modelos financieros." },
            { "name": "Monitor externo 24\" FHD", "priority": "rec", "reason": "Permite ver el dataset en una pantalla y el reporte en la otra." },
            { "name": "Hub USB-C con HDMI", "priority": "rec", "reason": "Para conectar tu notebook en salas de presentación y defensas de proyectos." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["ryzen 7", "core i7", "thinkbook", "thinkpad", "elitebook", "aspire", "16 gb"],
            "motivo": "Fluidez óptima para análisis de datos en Python/R, simulación de procesos y Power BI.",
            "badge": "Optimización & Datos"
        }
    },

    "visual_arts": {
        "scores": {"CPU": 8, "RAM": 8, "Storage": 8, "GPU": 7, "Battery": 7, "Display": 9},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#f59e0b", "Battery": "#22c55e", "Display": "#ec4899"},
        "alert": "<strong>Carrera de expresión visual y diseño:</strong> La precisión de color de la pantalla (100% sRGB / DCI-P3) es tan crucial como la potencia. Se requiere GPU dedicada o Apple Silicon para edición fluida en suite Adobe y 3D.",
        "software": ["Adobe Photoshop", "Adobe Illustrator", "Premiere Pro / After Effects", "Blender 3D", "Figma / InDesign"],
        "laptops": {
            "ideal": {
                "name": "Apple MacBook Air M2/M3 (16GB) / ASUS VivoBook Pro OLED",
                "cpu": "Apple M2/M3 o Intel Core i7 / Ryzen 7",
                "ram": "16 GB a 32 GB unificada/DDR5",
                "storage": "SSD NVMe 1TB",
                "gpu": "GPU Apple 10 núcleos o NVIDIA RTX 4050/4060",
                "battery": "~12-16 hrs (Mac) / ~8 hrs (ASUS)",
                "display": 'Pantalla Retina o OLED 2.8K 100% DCI-P3 calibrada de fábrica',
                "price": "$1.050.000 – $1.500.000",
                "why": "La fidelidad de color evita errores al imprimir o exponer. El renderizado de video y gráficos vectoriales vuela en esta configuración."
            },
            "balance": {
                "name": "ASUS VivoBook 15 OLED / Lenovo IdeaPad Slim 5",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5 13va gen",
                "ram": "16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados avanzados o NVIDIA RTX 3050",
                "battery": "~7-9 hrs",
                "display": '15.6" OLED FHD 100% DCI-P3 o IPS 100% sRGB',
                "price": "$600.000 – $850.000",
                "why": "Panel de color profesional a precio accesible, perfecto para ilustración digital y retoque fotográfico."
            },
            "eco": {
                "name": "Laptop estándar IPS FHD + Monitor externo calibrado",
                "cpu": "AMD Ryzen 5 o Intel Core i5",
                "ram": "16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~6-8 hrs",
                "display": '15.6" FHD IPS',
                "price": "$400.000 – $550.000",
                "why": "Permite trabajar diseño vectorial y maquetación digital de forma fluida."
            }
        },
        "tablets": [
            { "emoji": "🎨", "name": "Wacom Intuos / iPad 10ma con Apple Pencil", "reason": "Herramienta ESENCIAL para ilustración a mano, dibujo vectorial y retoque de texturas.", "price": "$80.000 – $380.000 CLP" }
        ],
        "calcs": [
            { "name": "Calculadora básica de bolsillo", "why": "No se requieren funciones avanzadas en artes visuales.", "price": "~$5.000 CLP" }
        ],
        "accessories": [
            { "name": "Tableta digitalizadora con lápiz sensible a la presión", "priority": "must", "reason": "La precisión respecto a un mouse convencional es abismal para ilustrar." },
            { "name": "Disco externo 1TB-2TB para proyectos multimedia", "priority": "must", "reason": "Archivos PSD, TIFF y secuencias de video ocupan cientos de gigabytes." },
            { "name": "Calibrador de color o monitor externo IPS", "priority": "rec", "reason": "Garantiza que lo que ves en pantalla sea idéntico al resultado impreso." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["oled", "dci-p3", "macbook", "vivobook pro", "yoga", "100% srgb", "rtx"],
            "motivo": "Excelente calibración de pantalla y fluidez para Adobe Creative Cloud, Blender y Figma.",
            "badge": "Color & Creatividad"
        }
    },

    "health_clinical": {
        "scores": {"CPU": 6, "RAM": 7, "Storage": 6, "GPU": 2, "Battery": 9, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera clínica y hospitalaria:</strong> La portabilidad, peso ultra liviano (<1.5 kg) y autonomía de batería (+9 hrs) son la máxima prioridad para turnos y rotaciones en centros de salud. La tablet/iPad es un aliado crítico.",
        "software": ["Complete Anatomy 3D", "UpToDate / ClinicalKey", "Visores DICOM (Radiografías)", "Mendeley / Zotero", "Office 365"],
        "laptops": {
            "ideal": {
                "name": "Apple MacBook Air M2 / ASUS ZenBook 14 OLED",
                "cpu": "Apple M2 o Intel Core i5/i7 EVO / Ryzen 7 (bajo consumo)",
                "ram": "16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados eficientes",
                "battery": "~12-16 hrs (batería para todo el día sin enchufe)",
                "display": '13.3" a 14" IPS / OLED antirreflejo',
                "price": "$850.000 – $1.150.000",
                "why": "Pesa apenas 1.2 kg, enciende al instante al abrir la tapa y dura toda la jornada en rotaciones hospitalarias."
            },
            "balance": {
                "name": "Lenovo IdeaPad Slim 5 / Acer Swift Go 14",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5-1335U",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~8-10 hrs",
                "display": '14" FHD IPS mate',
                "price": "$500.000 – $680.000",
                "why": "Excelente relación entre peso reducido, batería duradera y fluidez para atlas de anatomía 3D."
            },
            "eco": {
                "name": "Notebook ultra portátil 14\" i5/Ryzen 5 refurbished o entrada",
                "cpu": "Intel Core i5 o AMD Ryzen 5",
                "ram": "8 GB a 16 GB",
                "storage": "SSD 256GB / 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~6-8 hrs",
                "display": '14" FHD',
                "price": "$300.000 – $440.000",
                "why": "Ligero y económico para transportar en mochila médica a laboratorios y clases."
            }
        },
        "tablets": [
            { "emoji": "🩺", "name": "iPad 10ma gen o iPad Air con Apple Pencil — MUY RECOMENDADO", "reason": "Es la herramienta #1 de estudio en salud: atlas de anatomía 3D, fichas clínicas, apuntes sobre diapositivas y lectura de papers.", "price": "$320.000 – $580.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-82MS o fx-991CW", "why": "Para cálculo de dosis, diluciones farmacológicas y bioestadística en primeros años.", "price": "~$18.000 – $35.000 CLP" }
        ],
        "accessories": [
            { "name": "Lápiz digital con rechazo de palma para tablet", "priority": "must", "reason": "Anotar esquemas clínicos a mano mejora la retención anatómica un 100%." },
            { "name": "Funda antigolpes para tablet/laptop", "priority": "must", "reason": "Protección para traslados continuos entre campus UdeC y campos clínicos." },
            { "name": "Cargador compacto GaN USB-C de 65W", "priority": "rec", "reason": "Carga tu celular, tablet y laptop con un solo cargador liviano en la mochila." }
        ],
        "db_profile": {
            "min_ram": 8,
            "gpu_dedicada": False,
            "peso_max": 1.6,
            "palabras_clave": ["macbook", "zenbook", "swift", "yoga", "ideapad slim", "ipad"],
            "motivo": "Gran autonomía de batería y peso ultra ligero para rondas hospitalarias, seminarios y atlas 3D.",
            "badge": "Ultra Portátil Clínico"
        }
    },

    "life_sciences": {
        "scores": {"CPU": 7, "RAM": 7, "Storage": 7, "GPU": 3, "Battery": 8, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera científica y biológica:</strong> Utilizarás software de bioestadística (RStudio, GraphPad), análisis de secuencias bioinformáticas, química estructural y procesamiento de imágenes microscópicas (ImageJ).",
        "software": ["RStudio / GraphPad Prism", "ChemDraw / PyMOL", "ImageJ (microscopía)", "Bioinformática / BLAST", "Mendeley / Zotero"],
        "laptops": {
            "ideal": {
                "name": "Lenovo ThinkPad E14 / ASUS ZenBook 14",
                "cpu": "AMD Ryzen 7 7730U o Intel Core i7 13va gen",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB / 1TB",
                "gpu": "Gráficos integrados",
                "battery": "~10-12 hrs",
                "display": '14"-15.6" FHD IPS mate',
                "price": "$700.000 – $920.000",
                "why": "Chasis duradero para salidas a terreno y laboratorios de investigación, con batería para todo el día."
            },
            "balance": {
                "name": "Acer Aspire 5 / ASUS VivoBook 15",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5-1235U",
                "ram": "16 GB DDR4",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$480.000 – $680.000",
                "why": "Excelente desempeño para correlaciones estadísticas, curvas de calibración y modelos moleculares en 3D."
            },
            "eco": {
                "name": "Notebook Ryzen 5 con SSD",
                "cpu": "AMD Ryzen 5 5500U",
                "ram": "8 GB (ampliable)",
                "storage": "SSD 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-8 hrs",
                "display": '15.6" FHD',
                "price": "$340.000 – $460.000",
                "why": "Resuelve holgadamente los informes de laboratorio, hojas de cálculo y papers."
            }
        },
        "tablets": [
            { "emoji": "🔬", "name": "Samsung Galaxy Tab S9 FE o iPad 10ma", "reason": "Excelente para registrar datos en terreno o mesón de laboratorio sin el estorbo de una laptop grande.", "price": "$280.000 – $390.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "Imprescindible para Química General, Orgánica, Físico-Química y Bioquímica (regresiones lineales, equilibrios iónicos).", "price": "~$32.000 – $42.000 CLP" }
        ],
        "accessories": [
            { "name": "Mouse óptico inalámbrico", "priority": "must", "reason": "Para conteo celular en ImageJ y selección precisa de moléculas en PyMOL." },
            { "name": "Funda resistente al agua para salidas a terreno / laboratorio", "priority": "must", "reason": "Protege tus equipos contra salpicaduras accidentales y condiciones de campo." },
            { "name": "Disco externo de respaldo", "priority": "rec", "reason": "Para fotos de geles de electroforesis y bases de datos experimentales." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["ryzen 5", "ryzen 7", "core i5", "core i7", "aspire", "vivobook", "thinkpad"],
            "motivo": "Fluidez para bioinformática, análisis estadístico R/GraphPad y modelado molecular.",
            "badge": "Ciencia & Laboratorio"
        }
    },

    "earth_exact_sciences": {
        "scores": {"CPU": 8, "RAM": 8, "Storage": 8, "GPU": 6, "Battery": 7, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#22c55e", "Battery": "#f59e0b", "Display": "#14b8a6"},
        "alert": "<strong>Carrera científica y de modelación espacial/terrestre:</strong> Manejarás grandes volúmenes de datos geoespaciales (QGIS, ArcGIS), simulaciones físicas en Python/MATLAB y análisis espectral o astronómico.",
        "software": ["Python (NumPy / SciPy)", "MATLAB / GNU Octave", "QGIS / ArcGIS", "LaTeX / Overleaf", "SAOImage DS9 / IRAF"],
        "laptops": {
            "ideal": {
                "name": "Lenovo Legion Slim 5 / ASUS TUF Gaming",
                "cpu": "AMD Ryzen 7 7840HS o Intel Core i7-13700H",
                "ram": "16 GB a 32 GB DDR5",
                "storage": "SSD NVMe 1TB PCIe",
                "gpu": "NVIDIA RTX 4050/4060 6GB+",
                "battery": "~6-8 hrs",
                "display": '15.6"-16" FHD/QHD IPS mate',
                "price": "$850.000 – $1.250.000",
                "why": "La GPU dedicada procesa capas raster GIS y paralelismo CUDA para simulaciones astronómicas o geofísicas en una fracción del tiempo."
            },
            "balance": {
                "name": "Acer Aspire 5 / ASUS VivoBook 15",
                "cpu": "AMD Ryzen 7 7730U o Intel Core i5 13va gen",
                "ram": "16 GB DDR4/DDR5",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados avanzados",
                "battery": "~8-10 hrs",
                "display": '15.6" FHD IPS',
                "price": "$520.000 – $750.000",
                "why": "Muy buen desempeño multicore para scripts de cálculo científico y procesamiento de mallas geológicas."
            },
            "eco": {
                "name": "Notebook Ryzen 5 con SSD NVMe",
                "cpu": "AMD Ryzen 5 5500U/7520U",
                "ram": "8 GB (ampliar a 16GB)",
                "storage": "SSD 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-8 hrs",
                "display": '15.6" FHD',
                "price": "$360.000 – $480.000",
                "why": "Responde con agilidad a ramos matemáticos y físicos de los primeros semestres."
            }
        },
        "tablets": [
            { "emoji": "📱", "name": "Tablet Samsung Galaxy Tab S6 Lite / iPad 10ma", "reason": "Excelente para resolución de problemas a mano alzada en cálculo y física, y cartografía en terreno.", "price": "$220.000 – $360.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-991CW ClassWiz", "why": "Cálculo integral numérico, matrices, vectores y constantes físicas universales preprogramadas.", "price": "~$32.000 – $42.000 CLP" }
        ],
        "accessories": [
            { "name": "Disco externo 1TB o 2TB de alta velocidad", "priority": "must", "reason": "Para imágenes satelitales multiespectrales, cubos de datos astronómicos y registros sísmicos." },
            { "name": "Mouse ergonómico", "priority": "must", "reason": "Fundamental para digitalización de curvas de nivel y polígonos en QGIS." },
            { "name": "Mochila técnica para terreno", "priority": "must", "reason": "Protege el equipo en salidas de campo a cordillera o costa." }
        ],
        "db_profile": {
            "min_ram": 16,
            "gpu_dedicada": False,
            "palabras_clave": ["ryzen 7", "core i7", "aspire", "legion", "tuf", "qgis", "16 gb"],
            "motivo": "Potencia computacional para Python científico, mapas GIS, simulaciones geofísicas y astronomía.",
            "badge": "Datos Científicos & GIS"
        }
    },

    "law_humanities": {
        "scores": {"CPU": 5, "RAM": 6, "Storage": 6, "GPU": 2, "Battery": 9, "Display": 8},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera de lectura extensiva y redacción jurídica/social:</strong> La prioridad máxima es una pantalla mate antirreflejo para no cansar la vista tras 8 horas de lectura, un teclado ergonómico de alta precisión y batería para todo el día.",
        "software": ["Adobe Acrobat Pro / PDF24", "SPSS / Jamovi (estadística social)", "ATLAS.ti / NVivo (análisis cualitativo)", "Zotero / Mendeley (citas APA)", "Office 365"],
        "laptops": {
            "ideal": {
                "name": "Lenovo ThinkPad E14 / Apple MacBook Air M2",
                "cpu": "Intel Core i5 gen 12/13, AMD Ryzen 5 o Apple M2",
                "ram": "16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~12-15 hrs",
                "display": '14" FHD IPS mate antirreflejo con filtro de luz azul',
                "price": "$650.000 – $950.000",
                "why": "El teclado ThinkPad es legendario por su comodidad de tipeo en memorias y alegatos. Batería que no te deja botado en la biblioteca ni en tribunales."
            },
            "balance": {
                "name": "Lenovo IdeaPad Slim 3 / Acer Aspire 3 o 5",
                "cpu": "AMD Ryzen 5 7520U/7530U o Intel Core i3/i5",
                "ram": "8 GB a 16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-9 hrs",
                "display": '15.6" o 14" FHD mate',
                "price": "$380.000 – $550.000",
                "why": "Equipo liviano y silencioso que maneja cientos de páginas en PDF y múltiples pestañas de leyes y jurisprudencia sin esfuerzo."
            },
            "eco": {
                "name": "Notebook refurbished corporativo (ThinkPad T480/T490) con SSD",
                "cpu": "Intel Core i5 8va-10ma gen",
                "ram": "8 GB RAM",
                "storage": "SSD 256GB / 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~5-7 hrs",
                "display": '14" FHD IPS mate',
                "price": "$220.000 – $320.000",
                "why": "Para leer doctrinas, redactar informes y buscar jurisprudencia, un equipo corporativo con SSD vuela y ahorra mucho dinero."
            }
        },
        "tablets": [
            { "emoji": "📚", "name": "iPad 9a/10a gen o Kindle Paperwhite", "reason": "Excelente alternativa para transportar códigos legales (Civil, Penal, etc.) y leer jurisprudencia en cualquier lugar.", "price": "$120.000 – $340.000 CLP" }
        ],
        "calcs": [
            { "name": "Calculadora básica", "why": "Solo requerida esporádicamente para liquidaciones o estadística social básica.", "price": "~$6.000 CLP" }
        ],
        "accessories": [
            { "name": "Atril elevador para laptop", "priority": "must", "reason": "Mantiene la pantalla a la altura de los ojos y previene dolores cervicales tras horas de lectura jurídica." },
            { "name": "Teclado y mouse inalámbricos para el escritorio", "priority": "rec", "reason": "Comodidad total para redactar ensayos, recursos y memorias de título." },
            { "name": "Audífonos con cancelación de ruido", "priority": "opt", "reason": "Para aislar el ruido exterior y concentrarse al estudiar en la biblioteca." }
        ],
        "db_profile": {
            "min_ram": 8,
            "gpu_dedicada": False,
            "peso_max": 1.6,
            "palabras_clave": ["thinkpad", "macbook", "zenbook", "aspire", "vivobook", "ideapad slim"],
            "motivo": "Teclado ergonómico, pantalla mate descansada para lectura y batería para toda la jornada.",
            "badge": "Lectura & Batería"
        }
    },

    "education": {
        "scores": {"CPU": 5, "RAM": 6, "Storage": 6, "GPU": 2, "Battery": 8, "Display": 7},
        "scoreColors": {"CPU": "#6366f1", "RAM": "#8b5cf6", "Storage": "#06b6d4", "GPU": "#64748b", "Battery": "#22c55e", "Display": "#f59e0b"},
        "alert": "<strong>Carrera docente y pedagógica:</strong> Necesitarás un equipo ágil para preparar material didáctico multimedia, guías, planificaciones curriculares y conectarlo frecuentemente a proyectores de colegios.",
        "software": ["Canva Pro / Genially", "Google Workspace / Classroom", "Microsoft Teams / Zoom", "GeoGebra (matemáticas)", "Office 365"],
        "laptops": {
            "ideal": {
                "name": "ASUS VivoBook 14/15 / Lenovo IdeaPad Slim 5",
                "cpu": "AMD Ryzen 5 7530U o Intel Core i5 12va/13va gen",
                "ram": "16 GB RAM",
                "storage": "SSD NVMe 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~8-10 hrs",
                "display": '14"-15.6" FHD IPS mate',
                "price": "$480.000 – $680.000",
                "why": "16GB de RAM aseguran que Canva, diapositivas pesadas y decenas de pestañas de investigación educativa corran simultáneamente sin trabas."
            },
            "balance": {
                "name": "Acer Aspire 3 / HP 15",
                "cpu": "AMD Ryzen 3/5 o Intel Core i3/i5",
                "ram": "8 GB a 16 GB",
                "storage": "SSD 512GB",
                "gpu": "Gráficos integrados",
                "battery": "~7-8 hrs",
                "display": '15.6" FHD',
                "price": "$360.000 – $480.000",
                "why": "Confiable, rápido para crear presentaciones y con puerto HDMI nativo para conectar proyectores."
            },
            "eco": {
                "name": "Notebook refurbished con SSD",
                "cpu": "Intel Core i5 o AMD Ryzen 3/5",
                "ram": "8 GB RAM",
                "storage": "SSD 256GB",
                "gpu": "Gráficos integrados",
                "battery": "~5-6 hrs",
                "display": '14" FHD',
                "price": "$220.000 – $320.000",
                "why": "Suficiente para redactar planificaciones, preparar evaluaciones y reuniones online."
            }
        },
        "tablets": [
            { "emoji": "🎒", "name": "Tablet Samsung Galaxy Tab A9+ o iPad 9a", "reason": "Excelente para pasar asistencia, proyectar recursos visuales en la sala de clases y corregir guías digitalmente.", "price": "$160.000 – $280.000 CLP" }
        ],
        "calcs": [
            { "name": "Casio fx-82MS / fx-991CW", "why": "Casio científica estándar (indispensable para menciones en Matemáticas o Ciencias).", "price": "~$18.000 – $35.000 CLP" }
        ],
        "accessories": [
            { "name": "Puntero láser inalámbrico con control de diapositivas", "priority": "must", "reason": "Permite moverte libremente por la sala de clases mientras presentas material." },
            { "name": "Adaptador HDMI / VGA a USB-C", "priority": "must", "reason": "Los proyectores de colegios e institutos muchas veces usan cables VGA antiguos o HDMI estándar." },
            { "name": "Mochila universitaria acolchada", "priority": "rec", "reason": "Para transportar de forma segura tu computador y materiales didácticos a las prácticas pedagógicas." }
        ],
        "db_profile": {
            "min_ram": 8,
            "gpu_dedicada": False,
            "peso_max": 1.7,
            "palabras_clave": ["aspire", "vivobook", "ideapad", "galaxy book", "swift"],
            "motivo": "Ligero, con HDMI y batería duradera para planificaciones docentes y presentaciones en aula.",
            "badge": "Docencia & Aula"
        }
    }
}

# Mapeo de cada una de las 92 carreras oficiales a su familia técnica
CAREER_MAP = {
    # ─── CAMPUS CONCEPCIÓN (74 carreras) ───
    "administracion-publica-y-ciencia-politica": ("business_quant", "Administración Pública y Ciencia Política"),
    "agronomia-concepcion": ("life_sciences", "Agronomía"),
    "agronomia": ("life_sciences", "Agronomía"),
    "antropologia": ("law_humanities", "Antropología"),
    "arquitectura": ("cad_heavy", "Arquitectura"),
    "artes-visuales": ("visual_arts", "Artes Visuales"),
    "astronomia": ("earth_exact_sciences", "Astronomía"),
    "auditoria": ("business_quant", "Auditoría"),
    "bachillerato-en-ciencias-e-innovacion": ("earth_exact_sciences", "Bachillerato en Ciencias e Innovación"),
    "bachillerato-en-humanidades": ("law_humanities", "Bachillerato en Humanidades"),
    "bioingenieria": ("life_sciences", "Bioingeniería"),
    "biologia": ("life_sciences", "Biología"),
    "biologia-marina": ("life_sciences", "Biología Marina"),
    "bioquimica": ("life_sciences", "Bioquímica"),
    "ciencias-fisicas": ("earth_exact_sciences", "Ciencias Físicas"),
    "derecho": ("law_humanities", "Derecho"),
    "educacion-general-basica": ("education", "Educación General Básica"),
    "educacion-diferencial": ("education", "Educación Diferencial"),
    "educacion-parvularia": ("education", "Educación Parvularia"),
    "enfermeria": ("health_clinical", "Enfermería"),
    "fonoaudiologia": ("health_clinical", "Fonoaudiología"),
    "geofisica": ("earth_exact_sciences", "Geofísica"),
    "geografia": ("earth_exact_sciences", "Geografía"),
    "geologia": ("earth_exact_sciences", "Geología"),
    "ingenieria-ambiental": ("process_eng", "Ingeniería Ambiental"),
    "ingenieria-civil-primer-ano-comun": ("cad_heavy", "Ingeniería Civil — Primer Año Común"),
    "ingenieria-civil": ("cad_heavy", "Ingeniería Civil"),
    "ingenieria-civil-aeroespacial": ("cad_heavy", "Ingeniería Civil Aeroespacial"),
    "ingenieria-civil-biomedica": ("electronics", "Ingeniería Civil Biomédica"),
    "ingenieria-civil-de-materiales": ("cad_heavy", "Ingeniería Civil de Materiales"),
    "ingenieria-civil-de-minas": ("cad_heavy", "Ingeniería Civil de Minas"),
    "ingenieria-civil-electrica": ("electronics", "Ingeniería Civil Eléctrica"),
    "ingenieria-civil-electronica": ("electronics", "Ingeniería Civil Electrónica"),
    "ingenieria-civil-en-telecomunicaciones": ("electronics", "Ingeniería Civil en Telecomunicaciones"),
    "ingenieria-civil-industrial": ("business_quant", "Ingeniería Civil Industrial"),
    "ingenieria-civil-informatica": ("software_dev", "Ingeniería Civil Informática"),
    "ingenieria-civil-matematica": ("earth_exact_sciences", "Ingeniería Civil Matemática"),
    "ingenieria-civil-mecanica": ("cad_heavy", "Ingeniería Civil Mecánica"),
    "ingenieria-civil-metalurgica": ("cad_heavy", "Ingeniería Civil Metalúrgica"),
    "ingenieria-civil-quimica": ("process_eng", "Ingeniería Civil Química"),
    "ingenieria-comercial": ("business_quant", "Ingeniería Comercial"),
    "ingenieria-en-biotecnologia-marina-y-acuicultura": ("life_sciences", "Ingeniería en Biotecnología Marina y Acuicultura"),
    "ingenieria-en-biotecnologia-vegetal": ("life_sciences", "Ingeniería en Biotecnología Vegetal"),
    "ingenieria-en-conservacion-de-recursos-naturales": ("process_eng", "Ingeniería en Conservación de Recursos Naturales"),
    "ingenieria-estadistica": ("business_quant", "Ingeniería Estadística"),
    "ingenieria-forestal": ("process_eng", "Ingeniería Forestal"),
    "kinesiologia": ("health_clinical", "Kinesiología"),
    "licenciatura-en-historia": ("law_humanities", "Licenciatura en Historia"),
    "licenciatura-en-matematica": ("earth_exact_sciences", "Licenciatura en Matemática"),
    "licenciatura-en-quimica-quimico": ("life_sciences", "Licenciatura en Química / Químico"),
    "medicina": ("health_clinical", "Medicina"),
    "medicina-veterinaria": ("life_sciences", "Medicina Veterinaria"),
    "nutricion-y-dietetica": ("health_clinical", "Nutrición y Dietética"),
    "obstetricia-y-puericultura": ("health_clinical", "Obstetricia y Puericultura"),
    "odontologia": ("health_clinical", "Odontología"),
    "pedagogia-en-artes-visuales": ("visual_arts", "Pedagogía en Artes Visuales"),
    "pedagogia-en-ciencias-naturales-y-biologia": ("education", "Pedagogía en Ciencias Naturales y Biología"),
    "pedagogia-en-ciencias-naturales-y-fisica": ("education", "Pedagogía en Ciencias Naturales y Física"),
    "pedagogia-en-ciencias-naturales-y-quimica": ("education", "Pedagogía en Ciencias Naturales y Química"),
    "pedagogia-en-educacion-fisica": ("education", "Pedagogía en Educación Física"),
    "pedagogia-en-educacion-musical": ("education", "Pedagogía en Educación Musical"),
    "pedagogia-en-espanol": ("education", "Pedagogía en Español"),
    "pedagogia-en-filosofia": ("education", "Pedagogía en Filosofía"),
    "pedagogia-en-historia-y-geografia": ("education", "Pedagogía en Historia y Geografía"),
    "pedagogia-en-ingles": ("education", "Pedagogía en Inglés"),
    "pedagogia-en-matematicas": ("education", "Pedagogía en Matemáticas"),
    "periodismo": ("law_humanities", "Periodismo"),
    "psicologia": ("law_humanities", "Psicología"),
    "quimica-y-farmacia": ("life_sciences", "Química y Farmacia"),
    "quimico-a-analista": ("life_sciences", "Químico/a Analista"),
    "sociologia": ("law_humanities", "Sociología"),
    "teatro": ("visual_arts", "Teatro"),
    "tecnologia-medica": ("health_clinical", "Tecnología Médica"),
    "traduccion-interpretacion-en-idiomas-extranjeros": ("law_humanities", "Traducción / Interpretación en Idiomas Extranjeros"),
    "trabajo-social": ("law_humanities", "Trabajo Social"),

    # ─── CAMPUS CHILLÁN (7 carreras) ───
    "agronomia-chillan": ("life_sciences", "Agronomía — Chillán"),
    "derecho-2": ("law_humanities", "Derecho — Chillán"),
    "derecho-chillan": ("law_humanities", "Derecho — Chillán"),
    "enfermeria-chillan": ("health_clinical", "Enfermería — Chillán"),
    "ingenieria-ambiental-chillan": ("process_eng", "Ingeniería Ambiental — Chillán"),
    "ingenieria-civil-agricola": ("cad_heavy", "Ingeniería Civil Agrícola — Chillán"),
    "ingenieria-comercial-chillan": ("business_quant", "Ingeniería Comercial — Chillán"),
    "medicina-veterinaria-chillan": ("life_sciences", "Medicina Veterinaria — Chillán"),

    # ─── CAMPUS LOS ÁNGELES (11 carreras) ───
    "auditoria-diurna": ("business_quant", "Auditoría — Los Ángeles"),
    "auditoria-los-angeles": ("business_quant", "Auditoría — Los Ángeles"),
    "educacion-general-basica-los-angeles": ("education", "Educación General Básica — Los Ángeles"),
    "educacion-diferencial-los-angeles": ("education", "Educación Diferencial — Los Ángeles"),
    "enfermeria-los-angeles": ("health_clinical", "Enfermería — Los Ángeles"),
    "ingenieria-comercial-los-angeles": ("business_quant", "Ingeniería Comercial — Los Ángeles"),
    "ingenieria-en-biotecnologia-vegetal-2": ("life_sciences", "Ingeniería en Biotecnología Vegetal — Los Ángeles"),
    "ingenieria-en-biotecnologia-vegetal-los-angeles": ("life_sciences", "Ingeniería en Biotecnología Vegetal — Los Ángeles"),
    "ingenieria-geomatica": ("cad_heavy", "Ingeniería Geomática — Los Ángeles"),
    "pedagogia-en-ciencias-naturales-y-biologia-los-angeles": ("education", "Pedagogía en Ciencias Naturales y Biología — Los Ángeles"),
    "pedagogia-en-espanol-los-angeles": ("education", "Pedagogía en Español — Los Ángeles"),
    "pedagogia-en-ingles-los-angeles": ("education", "Pedagogía en Inglés — Los Ángeles"),
    "pedagogia-en-matematicas-los-angeles": ("education", "Pedagogía en Matemáticas — Los Ángeles"),

    # Compatibilidad con claves históricas anteriores
    "ing_civil_industrial": ("business_quant", "Ingeniería Civil Industrial"),
    "ing_civil_informatica": ("software_dev", "Ingeniería Civil Informática"),
    "ing_mecanica": ("cad_heavy", "Ingeniería Civil Mecánica"),
    "ing_electrica": ("electronics", "Ingeniería Civil Eléctrica"),
    "ing_quimica": ("process_eng", "Ingeniería Civil Química"),
    "ing_comercial": ("business_quant", "Ingeniería Comercial"),
    "diseno_grafico": ("visual_arts", "Artes Visuales & Diseño"),
    "administracion": ("business_quant", "Administración Pública"),
    "contabilidad": ("business_quant", "Auditoría"),
    "economia": ("business_quant", "Ingeniería Comercial"),
    "cine": ("visual_arts", "Artes Visuales & Multimedia"),
    "pedagogia": ("education", "Pedagogía General"),
}

# Construir diccionario unificado de CAREERS para recomendador.html
full_careers_js = {}

# Leer los datos de raw_carreras
for rc in raw_carreras:
    href = rc.get("href", "").rstrip("/")
    slug = href.split("/")[-1] if href else rc["title"].lower().replace(" ", "-")
    campus = rc.get("campus", "Campus Concepción")
    title = rc.get("title", slug)

    mapping = CAREER_MAP.get(slug)
    if not mapping:
        # Fallback a búsqueda parcial
        for k, v in CAREER_MAP.items():
            if k in slug or slug in k:
                mapping = v
                break
    
    family_key, clean_title = mapping if mapping else ("business_quant", title)
    fam = FAMILIES[family_key]

    full_careers_js[slug] = {
        "label": f"{clean_title}",
        "campus": campus,
        "url": rc.get("href") or f"https://admision.udec.cl/{slug}/",
        "family": family_key,
        "alert": fam["alert"],
        "scores": fam["scores"],
        "scoreColors": fam["scoreColors"],
        "software": fam["software"],
        "laptops": fam["laptops"],
        "tablets": fam["tablets"],
        "calcs": fam["calcs"],
        "accessories": fam["accessories"]
    }

# Agregar retrocompatibilidad para claves existentes
for old_key, (fam_key, label) in CAREER_MAP.items():
    if old_key not in full_careers_js:
        fam = FAMILIES[fam_key]
        full_careers_js[old_key] = {
            "label": label,
            "campus": "Campus Concepción",
            "url": "https://admision.udec.cl/carreras-udec/",
            "family": fam_key,
            "alert": fam["alert"],
            "scores": fam["scores"],
            "scoreColors": fam["scoreColors"],
            "software": fam["software"],
            "laptops": fam["laptops"],
            "tablets": fam["tablets"],
            "calcs": fam["calcs"],
            "accessories": fam["accessories"]
        }

print(f"Total carreras procesadas para recomendador.html: {len(full_careers_js)}")

# Construir PERFILES_CARRERAS para db_mock.py
full_db_profiles = {}
for slug, data in full_careers_js.items():
    fam = FAMILIES[data["family"]]
    prof = dict(fam["db_profile"])
    prof["nombre"] = data["label"]
    prof["campus"] = data["campus"]
    prof["url"] = data["url"]
    full_db_profiles[slug] = prof

print(f"Total perfiles para db_mock.py: {len(full_db_profiles)}")

# Guardar en archivo JSON de datos de referencia
with open("udec_carreras_full.json", "w", encoding="utf-8") as out:
    json.dump({
        "careers": full_careers_js,
        "db_profiles": full_db_profiles
    }, out, ensure_ascii=False, indent=2)

print("Datos exportados exitosamente a udec_carreras_full.json")
