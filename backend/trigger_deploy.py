import urllib.request, json

headers = {
    'Authorization': 'Bearer rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
body = json.dumps({}).encode()
req = urllib.request.Request(
    'https://api.render.com/v1/services/srv-da215jbl550s73avpr40/deploys',
    data=body, headers=headers, method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode())
    deploy_id = result.get('id', 'unknown')
    status = result.get('status', 'unknown')
    print(f'Deploy triggered: {deploy_id}')
    print(f'Status: {status}')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
