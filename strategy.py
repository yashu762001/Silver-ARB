from kiteconnect import KiteConnect
import json
import config

API_KEY = config.API_KEY

# initialize kite
kite = KiteConnect(api_key=API_KEY)

# load access token
with open("token.json") as f:
    access_token = json.load(f)["access_token"]

kite.set_access_token(access_token)

try:
    # fetch LTP
    prods = ["NSE:INFY", "NSE:RELIANCE","MCX:SILVER26MAYFUT", "MCX:SILVERM26APRFUT"]
    ltp_data = kite.ltp(prods)

    print("Access token is working!\n")

    try:
        for prod in prods:
            print(prod, " ", ltp_data[prod]["last_price"])

    except Exception as e:
        print(e)

except Exception as e:
    print("Access token invalid or expired")
    print("Error:", e)