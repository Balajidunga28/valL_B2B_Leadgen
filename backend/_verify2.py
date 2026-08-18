import urllib.request, json, time

# 1. Login
data = json.dumps({"email": "admin@vallg.com", "password": "admin123"}).encode()
req = urllib.request.Request("https://vallg-api.onrender.com/api/auth/login", data=data, headers={"Content-Type": "application/json", "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
token = json.loads(resp.read().decode())["token"]
print("1. Login OK")

# 2. Warm up with health check
req = urllib.request.Request("https://vallg-api.onrender.com/api/health", headers={"Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
print("2. Health:", json.loads(resp.read().decode()))

# 3. Run search with long timeout
print("3. Running search (may take up to 5 min for cold start + pipeline)...")
start = time.time()
data = json.dumps({"query": "Hospitals in Eluru", "location": "Eluru, Andhra Pradesh"}).encode()
req = urllib.request.Request("https://vallg-api.onrender.com/api/search", data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token, "Accept": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=300)
    result = json.loads(resp.read().decode())
    elapsed = time.time() - start
    print(f"   Search completed in {elapsed:.1f}s: {result['total_count']} raw records")
except Exception as e:
    elapsed = time.time() - start
    print(f"   Search failed after {elapsed:.1f}s: {e}")
    
    # Check if leads were created anyway (pipeline might have partially completed)
    print("   Checking if companies exist despite timeout...")
    req = urllib.request.Request("https://vallg-api.onrender.com/api/leads", headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
    resp = urllib.request.urlopen(req, timeout=60)
    leads = json.loads(resp.read().decode())
    print("   Leads:", len(leads))
    if leads:
        for l in leads[:5]:
            print("   -", l["name"], "| score=", l["total_score"])
    exit(0)

# 4. Check leads
req = urllib.request.Request("https://vallg-api.onrender.com/api/leads", headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
leads = json.loads(resp.read().decode())
print(f"4. Leads returned: {len(leads)}")
for lead in leads[:5]:
    print(f"   - {lead['name']} | score={lead['total_score']} | source={lead['source']} | city={lead['city']}")

# 5. Stats
req = urllib.request.Request("https://vallg-api.onrender.com/api/leads/stats", headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
stats = json.loads(resp.read().decode())
print(f"5. Stats: {json.dumps(stats, indent=2)}")
