import re
import json

with open('recomendador.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all select elements
select_matches = re.findall(r'<select[^>]*>(.*?)</select>', html, re.DOTALL)
print(f'Total select elements found: {len(select_matches)}')

career_select = None
for s in select_matches:
    if 'odontologia' in s or 'geologia' in s:
        career_select = s
        break

if not career_select:
    print('ERROR: career selector element not found')
    exit(1)

options = re.findall(r'<option\s+value="([^"]+)"', career_select)
options = [opt for opt in options if opt and opt != ""]
print(f'Total valid <option> careers in selector: {len(options)}')

# Extract CAREERS from HTML
careers_match = re.search(r'var CAREERS = (\{.*?\});\n\n\s+var currentRecCarrera', html, re.DOTALL)
if not careers_match:
    print('ERROR: CAREERS JS object not found')
    exit(1)

careers_data = json.loads(careers_match.group(1))
print(f'Total keys in CAREERS JS object: {len(careers_data)}')

missing = [opt for opt in options if opt not in careers_data]
if missing:
    print(f'ERROR: {len(missing)} options missing in CAREERS: {missing}')
    exit(1)
else:
    print(f'SUCCESS: All {len(options)} career select options match 100% in CAREERS dictionary!')

# Sample diverse careers (from different faculties and campuses)
sample_keys = [
    'geologia',
    'odontologia',
    'ingenieria-civil-aeroespacial',
    'ingenieria-civil-biomedica',
    'medicina-veterinaria-chillan',
    'pedagogia-en-ciencias-naturales-y-biologia-los-angeles',
    'astronomia',
    'arquitectura',
    'derecho',
    'derecho-2',
    'quimica-y-farmacia'
]

print('\n--- VERIFICATION OF SAMPLE DIVERSE CAREERS ---')
for k in sample_keys:
    c = careers_data[k]
    lbl = c.get('label', '')
    campus = c.get('campus', '')
    soft = ', '.join(c.get('software', []))
    raw_alert = c.get('alert', '')
    alert_clean = re.sub(r'<[^>]+>', '', raw_alert)[:95].strip()
    tab_len = len(c.get('tablets', []))
    calc_len = len(c.get('calcs', []))
    lap_ideal_why = c.get('laptops', {}).get('ideal', {}).get('why', '')[:60]
    print(f'[{k}] -> {lbl} ({campus})')
    print(f'   Software: {soft}')
    print(f'   Alert: {alert_clean}...')
    print(f'   Laptops Ideal: {lap_ideal_why}...')
    print(f'   Tablets: {tab_len} ref | Calcs: {calc_len} ref\n')
