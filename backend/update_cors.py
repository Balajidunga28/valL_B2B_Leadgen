import urllib.request, json

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"

headers = {
    "Authorization": f"Bearer {RENDER_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Update CORS with actual frontend URL
body = json.dumps({"value": "https://vallg-frontend.pages.dev,https://72d731c4.vallg-frontend.pages.dev,https://f312d2c1.vallg-frontend.pages.dev,https://vallg-api.onrender.com"}).encode()
req = urllib.request.Request(
    f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/CORS_ORIGINS",
    data=body, headers=headers, method="PUT"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print("CORS updated with all frontend URLs")
except urllib.error.HTTPError as e:
    print(f"CORS update failed: {e.read().decode()}")

# Trigger redeploy
body2 = json.dumps({}).encode()
req2 = urllib.request.Request(
    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
    data=body2, headers=headers, method="POST"
)
try:
    resp2 = urllib.request.urlopen(req2, timeout=30)
    result = json.loads(resp2.read().decode())
    print(f"Redeploy triggered: {result.get('id')}")
except urllib.error.HTTPError as e:
    print(f"Redeploy failed: {e.read().decode()}")
