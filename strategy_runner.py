import time
from market_data_engine import MarketDataEngine
from spread_engine import SpreadEngine
from signal_engine import SignalEngine
from execution_engine import initialize_execution_engine, execute_order, get_execution_info
from risk_manager import check_risk
from market_feed import MarketFeed
import config
import json
# from strategy_parameters import params

# load access token
with open("token.json") as f:
    access_token = json.load(f)["access_token"]

API_KEY = config.API_KEY
ACCESS_TOKEN=access_token
ticks_duration = config.TICKS_DURATION
execution_duration=config.EXECUTION_CALL_DURATION
# def run_strategy(graph_queue, shared_params):
#     market_data_engine = MarketDataEngine()
#     spread_engine = SpreadEngine()
#     signal_engine = SignalEngine()
#     feed = MarketFeed(API_KEY, ACCESS_TOKEN, market_data_engine)
#     feed.start()

#     while True:

#         try:

#             price_a, price_b = market_data_engine.update()

#             spread_mean, spread = spread_engine.update(price_a, price_b)

#             if spread_mean is None:
#                 time.sleep(ticks_duration)
#                 continue
            
#             print("Sending spread to graph:", spread_mean)
#             graph_queue.put(spread_mean)

#             spread = 1e4*(price_a - price_b)/(0.5*(price_a + price_b))
#             signal = signal_engine.generate(spread, spread_mean, shared_params)
#             if signal is None:
#                 time.sleep(ticks_duration)
#                 continue

#             if not check_risk(signal, shared_params):
#                 time.sleep(ticks_duration)
#                 continue

#             execute_order(signal)

#         except Exception as e:

#             print("Strategy Error:", e)

#         time.sleep(ticks_duration)


def run_strategy(graph_queue, shared_params):

    market_data_engine = MarketDataEngine()
    spread_engine = SpreadEngine()
    signal_engine = SignalEngine()

    feed = MarketFeed(API_KEY, ACCESS_TOKEN, market_data_engine)
    feed.start()

    initialize_execution_engine(market_data_engine, shared_params)

    current_signal = None
    last_signal_time = 0
    last_execution_time = 0 

    while True:

        try:

            now = time.time()

            price_a, price_b = market_data_engine.update()

            # recompute fresh signal only every 30 sec
            if now - last_signal_time >= ticks_duration:

                last_signal_time = now
                current_signal = None

                if price_a is not None and price_b is not None:

                    spread_mean,spread = spread_engine.update(price_a, price_b)

                    if spread_mean is not None:
                        print("Sending spread to graph:", spread, flush=True)
                        graph_queue.put(spread)
                        position_silver, execution_spread = get_execution_info()
                        signal = signal_engine.generate(spread, spread_mean, shared_params, position_silver, execution_spread)

                        if signal is not None and check_risk(signal, shared_params):
                            current_signal = signal

            # execution engine runs continuously
            if now - last_execution_time >=execution_duration:
                last_execution_time = now
                execute_order(current_signal)

        except Exception as e:
            print("Strategy Error:", e, flush=True)