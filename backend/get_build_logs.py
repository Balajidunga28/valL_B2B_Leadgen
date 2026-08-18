import urllib.request, json, datetime

RENDER_KEY = "rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp"
SERVICE_ID = "srv-da215jbl550s73avpr40"
OWNER_ID = "tea-da210l1t0dsc73arsfdg"

end = datetime.datetime.utcnow().isoformat() + "Z"
start = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat() + "Z"

url = f"https://api.render.com/v1/logs?ownerId={OWNER_ID}&resource={SERVICE_ID}&type=build&startTime={start}&endTime={end}&limit=50"
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {RENDER_KEY}",
    "Accept": "application/json"
})
try:
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read().decode())
    logs = data.get("logs", [])
    if not logs:
        print("No build logs found")
    else:
        for log in logs:
            message = log.get("message", "")
            if message.strip():
                print(message.strip())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
