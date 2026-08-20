import requests
import config
import json

API_KEY = config.API_KEY
with open("token.json") as f:
    ACCESS_TOKEN = json.load(f)["access_token"]

url = "https://api.kite.trade/instruments"

headers = {
    "X-Kite-Version": "3",
    "Authorization": f"token {API_KEY}:{ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:

    with open("instruments.csv", "wb") as f:
        f.write(response.content)

    print("Instrument dump downloaded: instruments.csv")

else:
    print("Error:", response.text)