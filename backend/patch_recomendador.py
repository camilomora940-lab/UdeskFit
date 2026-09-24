"""
Script para actualizar recomendador.html con:
1. Las 92 carreras oficiales de la Universidad de Concepción por campus.
2. Buscador en tiempo real de carreras.
3. Objeto CAREERS completo con los 92 perfiles técnicos y de software.
4. Badge de campus y enlace directo a admision.udec.cl/{carrera}.
"""
import re
import json

with open('recomendador.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Leer las opciones de carreras y el script inyectado
with open('carrera_options.html', 'r', encoding='utf-8') as f:
    options_html = f.read().strip()

with open('backend/careers_inject.js', 'r', encoding='utf-8') as f:
    careers_js = f.read().strip()

# 2. Agregar CSS para badges
css_to_add = """
    .campus-badge {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 999px;
      background: rgba(34, 60, 106, 0.09);
      color: var(--udec-azul);
      border: 1px solid rgba(34, 60, 106, 0.22);
      margin-left: 8px;
      vertical-align: middle;
    }
    .udec-link-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #1d4ed8;
      text-decoration: none;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      padding: 5px 12px;
      border-radius: 8px;
      transition: all 0.2s ease;
    }
    .udec-link-badge:hover {
      background: #dbeafe;
      color: #1e40af;
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
    }
"""

if '.campus-badge' not in html:
    html = html.replace('/* ─── UDEC & GIIA FOOTER (FONDO BLANCO INSTITUCIONAL) ─── */', css_to_add + '\n    /* ─── UDEC & GIIA FOOTER (FONDO BLANCO INSTITUCIONAL) ─── */')

# 3. Actualizar el selector de carreras y agregar input de filtrado
old_select_pattern = re.compile(
    r'<label class="field-label">Carrera Universidad de Concepción</label>\s*<div class="select-wrap">\s*<select class="field-select" id="carreraSelect">[\s\S]*?</select>\s*</div>',
    re.MULTILINE
)

new_select_block = f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
            <label class="field-label" style="margin-bottom:0">Carrera Universidad de Concepción</label>
            <span style="font-size:0.75rem;color:var(--muted)">92 Carreras Oficiales (3 Campus)</span>
          </div>
          <input type="text" id="carreraSearchInput" class="field-input" placeholder="🔍 Escribe para filtrar carrera (ej: Informática, Agronomía, Chillán, Medicina)..." style="margin-bottom:8px;padding:9px 12px;font-size:0.86rem;border-radius:9px;border:1px solid #cbd5e1;width:100%;box-sizing:border-box;" oninput="filterCarreraOptions(this.value)">
          <div class="select-wrap">
            <select class="field-select" id="carreraSelect">
              <option value="">— Selecciona tu carrera oficial UdeC —</option>
{options_html}
            </select>
          </div>"""

if old_select_pattern.search(html):
    html = old_select_pattern.sub(new_select_block, html)
    print("Reemplazado selector de carreras con éxito.")
else:
    print("AVISO: No se encontró patrón old_select_pattern")

# 4. Actualizar result-header para incluir campus badge y enlace oficial
old_result_title = '<div class="result-title">Recomendación para <span id="resCarreraName"></span></div>'
new_result_title = """<div class="result-title">
          Recomendación para <span id="resCarreraName"></span>
          <span id="resCampusBadge" class="campus-badge"></span>
        </div>
        <div id="resOfficialLinkWrap" style="margin-top:6px;display:none;">
          <a id="resOfficialLink" href="#" target="_blank" rel="noopener noreferrer" class="udec-link-badge">
            🔗 Ver Malla Curricular y Perfil Oficial UdeC ↗
          </a>
        </div>"""

if old_result_title in html:
    html = html.replace(old_result_title, new_result_title)
    print("Actualizado result-header con badges UdeC.")

# 5. Reemplazar definición de CAREERS
old_careers_pattern = re.compile(r'var CAREERS = \{[\s\S]*?\n    \};', re.MULTILINE)
if old_careers_pattern.search(html):
    html = old_careers_pattern.sub(careers_js, html)
    print("Reemplazado bloque CAREERS con éxito.")
else:
    print("AVISO: No se encontró bloque var CAREERS = { ... };")

# 6. Agregar función filterCarreraOptions y actualizar generateRec para badges
filter_func_code = """
    function filterCarreraOptions(query) {
      var q = (query || '').toLowerCase().trim();
      var select = document.getElementById('carreraSelect');
      var groups = select.getElementsByTagName('optgroup');
      for (var i = 0; i < groups.length; i++) {
        var group = groups[i];
        var options = group.getElementsByTagName('option');
        var visibleInGroup = 0;
        for (var j = 0; j < options.length; j++) {
          var opt = options[j];
          var match = !q || opt.textContent.toLowerCase().indexOf(q) !== -1 || group.label.toLowerCase().indexOf(q) !== -1;
          opt.style.display = match ? '' : 'none';
          if (match) visibleInGroup++;
        }
        group.style.display = visibleInGroup > 0 ? '' : 'none';
      }
    }
"""

if 'function filterCarreraOptions' not in html:
    html = html.replace('function selectBudget(el) {', filter_func_code + '\n    function selectBudget(el) {')
    print("Inyectada función filterCarreraOptions.")

# En generateRec(), actualizar asignación de badges
target_gen_rec = "document.getElementById('resCarreraName').textContent = career.label;"
replacement_gen_rec = """document.getElementById('resCarreraName').textContent = career.label;
      if (document.getElementById('resCampusBadge')) {
        document.getElementById('resCampusBadge').textContent = career.campus || 'Campus Concepción';
      }
      if (document.getElementById('resOfficialLink') && career.url) {
        document.getElementById('resOfficialLink').href = career.url;
        var linkWrap = document.getElementById('resOfficialLinkWrap');
        if (linkWrap) linkWrap.style.display = 'block';
      }"""

if target_gen_rec in html:
    html = html.replace(target_gen_rec, replacement_gen_rec)
    print("Actualizado generateRec() con asignación de campus y enlace oficial.")

with open('recomendador.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("recomendador.html guardado exitosamente.")
