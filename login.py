from kiteconnect import KiteConnect
from playwright.sync_api import sync_playwright
import json
import warnings
import webbrowser
import config
warnings.filterwarnings("ignore")

API_KEY = config.API_KEY
API_SECRET = config.SECRET_KEY

kite = KiteConnect(api_key=API_KEY)

login_url = kite.login_url()
print("Opening Zerodha login page...")
webbrowser.open(login_url)