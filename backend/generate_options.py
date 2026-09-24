import json

with open('udec_carreras_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

careers = data['careers']

by_campus = {
    'Campus Concepción': [],
    'Campus Chillán': [],
    'Campus Los Ángeles': []
}

with open('carreras_udec_parsed.json', 'r', encoding='utf-8') as f:
    raw_list = json.load(f)

for rc in raw_list:
    href = rc.get('href', '').rstrip('/')
    slug = href.split('/')[-1] if href else rc['title'].lower().replace(' ', '-')
    campus = rc.get('campus', 'Campus Concepción')
    title = rc.get('title', slug)
    if campus in by_campus:
        by_campus[campus].append((slug, title))

opt_html = []
icons = {
    'Campus Concepción': '🏛️ Campus Concepción (74 carreras)',
    'Campus Chillán': '🌱 Campus Chillán (7 carreras)',
    'Campus Los Ángeles': '🌲 Campus Los Ángeles (11 carreras)'
}

for campus, items in by_campus.items():
    opt_html.append(f'              <optgroup label="{icons[campus]}">')
    for slug, title in items:
        opt_html.append(f'                <option value="{slug}">{title}</option>')
    opt_html.append('              </optgroup>')

full_html = '\n'.join(opt_html)
print(f'Generated {len(by_campus["Campus Concepción"])} + {len(by_campus["Campus Chillán"])} + {len(by_campus["Campus Los Ángeles"])} options')
with open('carrera_options.html', 'w', encoding='utf-8') as out:
    out.write(full_html)
print('Saved carrera_options.html')
