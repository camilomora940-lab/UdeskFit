import urllib.request

url = 'https://media.solotodo.com/media/products/2099180_picture_1750852134.avif'
for ref in [None, 'https://www.solotodo.cl/', 'file:///']:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        if ref:
            headers['Referer'] = ref
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = res.read()
            print("Referer:", ref, "-> Status:", res.status, "Content-Type:", res.headers.get("Content-Type"), "Bytes:", len(data))
    except Exception as e:
        print("Referer:", ref, "-> Error:", e)
