import random

# class MarketDataEngine:

#     def __init__(self):

#         self.price_a = 100
#         self.price_b = 100

#     def update(self):

#         # random walk
#         self.price_a += random.uniform(-0.5,0.5)
#         self.price_b += random.uniform(-0.5,0.5)

#         return self.price_a, self.price_b

# trying for actual trading version 2:
class MarketDataEngine:

    def __init__(self):

        self.silver_bid = None
        self.silver_ask = None
        self.mini_bid = None
        self.mini_ask = None

    def on_market_data(self, silver_bid, silver_ask, mini_bid, mini_ask):

        self.silver_bid = silver_bid
        self.silver_ask = silver_ask
        self.mini_bid = mini_bid
        self.mini_ask = mini_ask

    def update(self):

        if None in (
            self.silver_bid,
            self.silver_ask,
            self.mini_bid,
            self.mini_ask
        ):
            return None, None

        silver_mid = 0.5 * (self.silver_bid + self.silver_ask)
        mini_mid = 0.5 * (self.mini_bid + self.mini_ask)

        return silver_mid, mini_mid  
    
    def get_l1_snapshot(self):
        if None in (
            self.silver_bid,
            self.silver_ask,
            self.mini_bid,
            self.mini_ask
        ):
            return None

        return {
            "silver_bid": self.silver_bid,
            "silver_ask": self.silver_ask,
            "mini_bid": self.mini_bid,
            "mini_ask": self.mini_ask
        }