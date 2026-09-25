import urllib.request
import json

data = json.dumps({
    'bin_path': 'data/sample_kitti/sequences/00/velodyne/000000.bin',
    'label_path': 'data/sample_kitti/sequences/00/labels/000000.label',
    'num_points': None,
    'interpolate_to_full': True,
    'preview_points_limit': 12000
}).encode()

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/inference', data=data, headers={'Content-Type': 'application/json'})
try:
    res = urllib.request.urlopen(req)
    d = json.loads(res.read().decode())
    print('Success! Total points:', d.get('total_points'))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
except Exception as e:
    print('Error:', e)
