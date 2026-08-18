import urllib.request, json, sys

headers = {
    'Authorization': 'Bearer rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
body = json.dumps({
    'type': 'web_service',
    'name': 'vallg-api',
    'ownerId': 'tea-da210l1t0dsc73arsfdg',
    'repo': 'https://github.com/Balajidunga28/valL_B2B_Leadgen',
    'branch': 'main',
    'rootDir': 'backend',
    'autoDeploy': 'yes',
    'serviceDetails': {
        'env': 'python',
        'plan': 'free',
        'region': 'oregon',
        'envSpecificDetails': {
            'buildCommand': 'pip install -r requirements.txt',
            'startCommand': 'uvicorn app.main:app --host 0.0.0.0 --port $PORT'
        }
    }
}).encode()

req = urllib.request.Request('https://api.render.com/v1/services', data=body, headers=headers, method='POST')
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode())
    print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
    sys.exit(1)
