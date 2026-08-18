import urllib.request, json

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"

data = json.dumps({"PYTHON_VERSION": "3.12.7"}).encode()
req = urllib.request.Request(
    f"https://api.render.com/v1/services/{SERVICE_ID}",
    data=data,
    headers={
        "Authorization": f"Bearer {RENDER_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    method="PATCH"
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode())
    print(f"Python version set to: {result.get('envVars', [{}])}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
