import urllib.request, json

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"

data = json.dumps({}).encode()
req = urllib.request.Request(
    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
    data=data,
    headers={
        "Authorization": f"Bearer {RENDER_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode())
    print(f"Deploy: {result.get('id')}, Status: {result.get('status')}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:300]}")
