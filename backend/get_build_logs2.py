import urllib.request, json, datetime, sys

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"
OWNER_ID = "tea-da210l1t0dsc73arsfdg"

end = datetime.datetime.now(datetime.timezone.utc).isoformat()
start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()

url = f"https://api.render.com/v1/logs?ownerId={OWNER_ID}&resource={SERVICE_ID}&type=build&startTime={start}&endTime={end}&limit=100"
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {RENDER_KEY}",
    "Accept": "application/json"
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read().decode())
    logs = data.get("logs", [])
    for log in logs:
        message = log.get("message", "")
        if message.strip():
            try:
                sys.stdout.buffer.write((message.strip() + "\n").encode("utf-8", errors="replace"))
            except Exception:
                pass
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}", flush=True)
