import json
from bs4 import BeautifulSoup

with open('carreras_udec_raw.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

h4s = soup.find_all('h4')
result = []
for i, h4 in enumerate(h4s):
    a = h4.find('a')
    href = a['href'] if a and a.has_attr('href') else ''
    title = h4.get_text(strip=True)
    campus = 'Campus Concepción'
    for p in h4.find_all_previous('h1'):
        c_text = p.get_text(strip=True)
        if 'Campus' in c_text:
            campus = c_text
            break
    result.append({
        'index': i + 1,
        'title': title,
        'href': href,
        'campus': campus
    })

with open('carreras_udec_parsed.json', 'w', encoding='utf-8') as out:
    json.dump(result, out, ensure_ascii=False, indent=2)

print(f'Successfully parsed {len(result)} careers.')
for item in result[:20]:
    print(f"{item['index']}. [{item['campus']}] {item['title']} -> {item['href']}")
