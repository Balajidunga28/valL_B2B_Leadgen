import urllib.request, json

req = urllib.request.Request(
    'https://api.render.com/v1/services/srv-da215jbl550s73avpr40/deploys?limit=5',
    headers={'Authorization': 'Bearer rnd_1YFRJMw7v9v4qeSkBDoWbON1DCkp', 'Accept': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode())
for d in data:
    deploy = d.get('deploy', d)
    print(f"ID: {deploy.get('id')}  Status: {deploy.get('status')}  Created: {deploy.get('createdAt', '')[:19]}")
