import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/simulation/frame/000000')
res = urllib.request.urlopen(req)
d = json.loads(res.read().decode())

perc = d['perception']
print('Perception keys:', list(perc.keys()))
print('Detected objects count:', len(perc.get('objects', [])))
print('Front objects count:', len(perc.get('front_objects', [])))
print('Proximity status:', perc.get('proximity_status'))
if perc.get('objects'):
    print('Sample object #1:', perc['objects'][0])
