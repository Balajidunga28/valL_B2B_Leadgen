import urllib.request, json

# 1. Login
data = json.dumps({"email": "admin@vallg.com", "password": "admin123"}).encode()
req = urllib.request.Request("https://vallg-api.onrender.com/api/auth/login", data=data, headers={"Content-Type": "application/json", "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=30)
token = json.loads(resp.read().decode())["token"]
print("1. Login OK")

# 2. Run search (triggers full pipeline)
data = json.dumps({"query": "Hospitals in Eluru", "location": "Eluru, Andhra Pradesh"}).encode()
req = urllib.request.Request("https://vallg-api.onrender.com/api/search", data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=120)
result = json.loads(resp.read().decode())
print("2. Search:", result["total_count"], "raw records extracted")

# 3. Check leads (companies)
req = urllib.request.Request("https://vallg-api.onrender.com/api/leads", headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=30)
leads = json.loads(resp.read().decode())
print("3. Leads returned:", len(leads))
for lead in leads[:5]:
    print("   -", lead["name"], "| score=", lead["total_score"], "| source=", lead["source"], "| city=", lead["city"])

# 4. Check stats
req = urllib.request.Request("https://vallg-api.onrender.com/api/leads/stats", headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=30)
stats = json.loads(resp.read().decode())
print("4. Stats:", json.dumps(stats, indent=2))
