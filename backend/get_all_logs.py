import urllib.request, json, datetime, sys, urllib.parse

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"
OWNER_ID = "tea-da210l1t0dsc73arsfdg"

end = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

for logtype in ["app", "build", "request"]:
    url = f"https://api.render.com/v1/logs?ownerId={OWNER_ID}&resource={SERVICE_ID}&type={logtype}&startTime={urllib.parse.quote(start)}&endTime={urllib.parse.quote(end)}&limit=50"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {RENDER_KEY}",
        "Accept": "application/json"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        logs = data.get("logs", [])
        if logs:
            sys.stdout.buffer.write(f"\n=== {logtype.upper()} LOGS ({len(logs)} entries) ===\n".encode("utf-8"))
            for log in logs:
                message = log.get("message", "")
                if message.strip():
                    try:
                        sys.stdout.buffer.write((message.strip() + "\n").encode("utf-8", errors="replace"))
                    except Exception:
                        pass
    except urllib.error.HTTPError as e:
        sys.stdout.buffer.write(f"HTTP {e.code} for {logtype}\n".encode("utf-8"))
