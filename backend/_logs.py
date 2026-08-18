import urllib.request, json, datetime, urllib.parse

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"
OWNER_ID = "tea-da210l1t0dsc73arsfdg"

end = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

url = "https://api.render.com/v1/logs?ownerId=%s&resource=%s&type=app&startTime=%s&endTime=%s&limit=50" % (OWNER_ID, SERVICE_ID, urllib.parse.quote(start), urllib.parse.quote(end))
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + RENDER_KEY, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode())
logs = data.get("logs", [])
for log in logs:
    message = log.get("message", "")
    if message.strip():
        try:
            import sys
            sys.stdout.buffer.write((message.strip() + "\n").encode("utf-8", errors="replace"))
        except Exception:
            pass
