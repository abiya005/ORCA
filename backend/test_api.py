import requests
import time

time.sleep(2)
base = 'http://127.0.0.1:5000'

# Status check
s = requests.get(f'{base}/api/status').json()
print('STATUS:', s)

# Test all three simulation keys
for key in ['apk_malware_1', 'apk_malware_2', 'apk_clean_1']:
    r = requests.post(f'{base}/api/analyze-apk', data={'is_simulation': 'true', 'sim_key': key}).json()
    rep = r['report']
    print(f'\n[{key}]')
    print(f'  App     : {rep["appName"]}')
    print(f'  Badge   : {rep["badge"]}')
    print(f'  Score   : {rep["score"]}')
    print(f'  Threat  : {rep["threatClass"]}')
