from collections import deque
import numpy as np
import config
from datetime import datetime,date
a = config.TICKS_DURATION
b = config.PAST_SPREAD_CALCULATION_DURATION

c = int(b/a)
silver_expiry=datetime.strptime(config.SILVER_EXPIRY, "%Y-%m-%d").date()
mini_expiry=datetime.strptime(config.SILVERMINI_EXPIRY, "%Y-%m-%d").date()
today=date.today()

sil_diff = silver_expiry-today
mini_diff = mini_expiry-today

silver_days = sil_diff.days
mini_days = mini_diff.days


class SpreadEngine:

    def __init__(self):
        self.window_size = c   # based on config parameters.
        self.spread_queue = deque()
        self.currentPrices = []

    def update(self, price_a, price_b):
        p_a = price_a/(np.exp(0.055*silver_days/365.25))
        p_b = price_b/(np.exp(0.055*mini_days/365.25))
        spread = 1e4*(p_a - p_b)/(0.5*(p_a+p_b))

        # wait until 15 min data collected
        if len(self.spread_queue) < self.window_size:
            self.spread_queue.append(spread)
            self.currentPrices.append([price_a, price_b])
            return None, spread

        # copy data
        spreads = list(self.spread_queue)

        # sort
        spreads.sort()

        n = len(spreads)

        # remove bottom 5% and top 5%
        lower = int(0.05 * n)
        upper = int(0.95 * n)

        filtered = spreads[lower:upper]

        mean_spread = np.mean(filtered)

        # maintain rolling window
        # store spread
        self.spread_queue.append(spread)
        self.currentPrices.append([price_a, price_b])
        self.spread_queue.popleft()
        self.currentPrices.pop(0)
        
        # print("current queue")
        # print(self.currentPrices)
        # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        now = datetime.now().strftime("%H:%M:%S")
        print(now)
        print(f"Mean is {mean_spread} and current spread is {spread}")
        return mean_spread, spread