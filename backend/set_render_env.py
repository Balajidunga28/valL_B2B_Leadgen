import urllib.request, json, sys

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"

NEON_CONN = "postgresql://neondb_owner:npg_25oNaBDYzhus@ep-plain-waterfall-aymymw6b.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
NEON_ASYNC = "postgresql+asyncpg://neondb_owner:npg_25oNaBDYzhus@ep-plain-waterfall-aymymw6b.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

env_vars = [
    ("DATABASE_URL", NEON_CONN),
    ("DATABASE_URL_ASYNC", NEON_ASYNC),
    ("JWT_SECRET", "vallg-prod-jk8x2m9p4q7w1e5r3t6y0u8i2o4a7s1d3f5g"),
    ("CORS_ORIGINS", "https://vallg-frontend.pages.dev,https://vallg-api.onrender.com"),
    ("GOOGLE_PLACES_API_KEY", ""),
    ("DEBUG", "false"),
]

for key, value in env_vars:
    headers = {
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    body = json.dumps({"value": value}).encode()
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{key}"
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        print(f"  OK: {key} = {value[:40]}...")
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  FAIL: {key} -> HTTP {e.code}: {err}")
