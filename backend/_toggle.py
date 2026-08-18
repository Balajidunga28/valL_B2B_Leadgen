import urllib.request, json

data = json.dumps({"private": False}).encode()
req = urllib.request.Request(
    "https://api.github.com/repos/Balajidunga28/valL_B2B_Leadgen",
    data=data,
    headers={
        "Authorization": "token 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",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "valL-bot"
    },
    method="PATCH"
)
resp = urllib.request.urlopen(req, timeout=15)
result = json.loads(resp.read().decode())
print("Private:", result.get("private"))
