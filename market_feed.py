# from kiteconnect import KiteTicker
# from market_data_engine import MarketDataEngine
# import config

# class MarketFeed:

#     def __init__(self, api_key, access_token, market_engine):

#         self.market_engine = market_engine

#         self.kws = KiteTicker(api_key, access_token)

#         # MCX instrument tokens (replace with correct ones)
#         self.SILVER = config.SILVER_TOKEN
#         self.SILVER_MINI = config.SILVER_MINI_TOKEN

#         self.kws.on_ticks = self.on_ticks
#         self.kws.on_connect = self.on_connect

#     def on_connect(self, ws, response):

#         ws.subscribe([self.SILVER, self.SILVER_MINI])
#         ws.set_mode(ws.MODE_FULL, [self.SILVER, self.SILVER_MINI])

#     def on_ticks(self, ws, ticks):

#         silver_bid = None
#         silver_ask = None
#         mini_bid = None
#         mini_ask = None

#         for t in ticks:

#             token = t["instrument_token"]

#             bid = t["depth"]["buy"][0]["price"]
#             ask = t["depth"]["sell"][0]["price"]

#             if token == self.SILVER:
#                 silver_bid = bid
#                 silver_ask = ask

#             if token == self.SILVER_MINI:
#                 mini_bid = bid
#                 mini_ask = ask

#         if None not in (silver_bid, silver_ask, mini_bid, mini_ask):

#             self.market_engine.on_market_data(
#                 silver_bid,
#                 silver_ask,
#                 mini_bid,
#                 mini_ask
#             )

#     def start(self):

#         self.kws.connect(threaded=True)


# filal testing chal rhi isliye yeh market feed se replace kr rha : 
import time
import threading
import config
from mock_kite import MockKiteConnect


class MarketFeed:

    def __init__(self, api_key, access_token, market_engine):
        self.market_engine = market_engine
        self.kite = MockKiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.running = False

    def start(self):
        self.running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        while self.running:
            silver_quote = self.kite.quote(config.SILVER_TRADINGSYMBOL)
            mini_quote = self.kite.quote(config.SILVER_MINI_TRADINGSYMBOL)

            silver_bid = silver_quote[config.SILVER_TRADINGSYMBOL]["depth"]["buy"][0]["price"]
            silver_ask = silver_quote[config.SILVER_TRADINGSYMBOL]["depth"]["sell"][0]["price"]

            mini_bid = mini_quote[config.SILVER_MINI_TRADINGSYMBOL]["depth"]["buy"][0]["price"]
            mini_ask = mini_quote[config.SILVER_MINI_TRADINGSYMBOL]["depth"]["sell"][0]["price"]

            self.market_engine.on_market_data(
                silver_bid,
                silver_ask,
                mini_bid,
                mini_ask
            )

            print(
                f"[MOCK FEED] "
                f"silver=({silver_bid}, {silver_ask}) "
                f"mini=({mini_bid}, {mini_ask})",
                flush=True
            )

            time.sleep(1)