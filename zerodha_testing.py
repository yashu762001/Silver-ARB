from kiteconnect import KiteConnect
import config
import json

requestToken=config.REQUEST_TOKEN
api_key=config.API_KEY
secret=config.SECRET_KEY

kite = KiteConnect(api_key=api_key)

login_url = kite.login_url()
data = kite.generate_session(requestToken, api_secret=secret)
access_token = data["access_token"]
kite.set_access_token(access_token)

with open("token.json", "w") as f:
    json.dump({"access_token": access_token}, f)

print(kite.ltp("NSE:INFY"))
