import requests
headers = {"User-Agent": "python:digitalarrestscraper:v1.0 (by /u/researcher123)"}
url = "https://www.reddit.com/r/india/search.json?q=digital+arrest&restrict_sr=1&sort=new&limit=10"
response = requests.get(url, headers=headers)
print(response.status_code)
if response.status_code == 200:
    print(len(response.json().get('data', {}).get('children', [])))
