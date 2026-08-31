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
    print(f'\n[APK SIM: {key}]')
    print(f'  App     : {rep["appName"]}')
    print(f'  Badge   : {rep["badge"]}')
    print(f'  Score   : {rep["score"]}')
    print(f'  Threat  : {rep["threatClass"]}')

# Test Fake HR Analysis endpoint across all 4 scam platforms + REAL Campus Placement Drive
fake_hr_tests = [
    ("REAL Campus Placement (Christ Univ AvgVa Solutions)", "From: Placement Office SOET <placementoffice.soet@christuniversity.in>\nGreetings from the Centre for Placements and Career Guidance! We are pleased to inform you about a Campus Placement Opportunity with AvgVa Solutions for the position of Business Development Associate (BDA). Eligible Batches: All Branches. Mode: Campus recruitment / interview process. Complete application through Google Form link."),
    ("Fake Email Scam", "Dear Candidate, you have been selected for remote data role. Pay $250 advance deposit for software equipment Zelle wire transfer."),
    ("Fake LinkedIn Scam", "Hi software developer, please clone our interview technical assessment GitHub repo and run npm run setup with admin permissions."),
    ("Fake Telegram Scam", "Earn Rs 5000 daily by liking YouTube videos and rating Google Maps. Click t.me/vip_task_portal and send UPI ID."),
    ("Fake WhatsApp Scam", "Hello, WhatsApp voice call recruiter offering block deal stock investment. Download app from wa.me link.")
]

for label, sample_text in fake_hr_tests:
    res = requests.post(f'{base}/api/analyze-fake-hr', json={'text': sample_text}).json()
    if res.get('success'):
        rep = res['report']
        print(f'\n[FAKE HR TEST: {label}]')
        print(f'  Title    : {rep["title"]}')
        print(f'  Category : {rep["category"]}')
        print(f'  Badge    : {rep["badge"]}')
        print(f'  Score    : {rep["score"]}')
        print(f'  Indicators: {", ".join(rep["indicators"])}')
    else:
        print(f'\n[FAKE HR TEST: {label}] FAILED: {res}')

# Test Digital Arrest Analysis endpoint (REAL Advisory vs FAKE Extortion Threat)
da_tests = [
    ("REAL MHA Cyber Safety Advisory", "PUBLIC SAFETY ADVISORY - Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs. No Police, CBI, ED, or RBI officer conducts legal interrogations or arrests via Skype video calls. Concept of digital arrest does not exist under Indian law. Report cybercrime at cybercrime.gov.in or Helpline 1930."),
    ("FAKE Digital Arrest Threat", "Urgent Notice from CBI Cyber Crime Cell. Your Aadhaar card and bank accounts flagged in money laundering investigation. You are ordered to enter secure digital detention on Skype video call and transfer assets to verification reserve account.")
]

for label, sample_text in da_tests:
    res = requests.post(f'{base}/api/analyze-digital-arrest', json={'text': sample_text}).json()
    if res.get('success'):
        rep = res['report']
        print(f'\n[DIGITAL ARREST TEST: {label}]')
        print(f'  Title    : {rep["title"]}')
        print(f'  Category : {rep["category"]}')
        print(f'  Badge    : {rep["badge"]}')
        print(f'  Score    : {rep["score"]}')
        print(f'  Indicators: {", ".join(rep["indicators"])}')
    else:
        print(f'\n[DIGITAL ARREST TEST: {label}] FAILED: {res}')


