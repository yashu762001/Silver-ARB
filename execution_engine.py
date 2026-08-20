# new correct testing version : 
import json
import time
# from kiteconnect import KiteConnect
from mock_kite import MockKiteConnect as KiteConnect
from datetime import datetime,date
from datetime import datetime
import config
import numpy as np

_ENGINE = None
silver_lot=config.SILVER_LOT
mini_lot=config.SILVER_MINI_LOT
aggression=config.SILVER_PASSIVE_AGGRESSION
hedge_sleep_duration=config.HEDGE_SLEEP_DURATION
silver_symbol=config.SILVER_TRADINGSYMBOL
mini_symbol=config.SILVER_MINI_TRADINGSYMBOL
sqoff_aggressiveness=config.ACTIVE_SQOFF_AGGRESSIVENESS

silver_expiry=datetime.strptime(config.SILVER_EXPIRY, "%Y-%m-%d").date()
mini_expiry=datetime.strptime(config.SILVERMINI_EXPIRY, "%Y-%m-%d").date()
today=date.today()

sil_diff = silver_expiry-today
mini_diff = mini_expiry-today

silver_days = sil_diff.days
mini_days = mini_diff.days

def initialize_execution_engine(market_data_engine, shared_params):
    global _ENGINE
    _ENGINE = ExecutionEngine(market_data_engine, shared_params)
    open('spreadTrades.txt', 'w').close()


def execute_order(signal):
    global _ENGINE
    if _ENGINE is None:
        raise RuntimeError("Execution engine not initialized")
    _ENGINE.run(signal)

def get_execution_info():
    global _ENGINE
    if _ENGINE is None:
        return 0, None
    return _ENGINE.get_execution_info()


class ExecutionEngine:

    def __init__(self, market_data_engine, shared_params):

        self.market_data_engine = market_data_engine
        self.params = shared_params
        with open("token.json") as f:
            access_token = json.load(f)["access_token"]

        self.kite = KiteConnect(api_key=config.API_KEY)
        self.kite.set_access_token(access_token)

        self.state = "IDLE"          # IDLE / WORKING / IN_POSITION
        self.side = None             # BUY / SELL for current working silver order
        self.mode = None             # OPEN / CLOSE

        self.sqoff_mode = None          # None / PASSIVE / AGGRESSIVE
        self.sqoff_trigger_pnl = None
        self.stoploss = config.STOPLOSS
        self.stoploss_improvement_pct = config.STOPLOSS_IMPROVEMENT_PCT
        self.stoploss_aggressive_pct = config.STOPLOSS_AGGRESSIVE_PCT

        self.passive_order_id = None
        self.passive_price = None
        self.silverExecutionPrice = 0
        self.silverMiniExecutionPrice = 0 
        self.executionSpread = None

        self.position_silver = 0
        self.position_mini = 0

        self.position_limit = config.POSITION_LIMIT
        self.ioc_width = config.IOC_WIDTH

        self.timebasedSqoff = None  # time based sqoff YES/None.

    def _get_total_pnl(self):

        positions = self.kite.positions()["net"]

        silver_pnl = 0
        mini_pnl = 0

        for p in positions:
            ts = p["tradingsymbol"]

            if ts == silver_symbol:
                silver_pnl = p["pnl"]

            elif ts == mini_symbol:
                mini_pnl = p["pnl"]

        return silver_pnl + mini_pnl
    
    def get_execution_info(self):
        return self.position_silver, self.executionSpread

    def run(self, signal):
        
        pnl = self._get_total_pnl()
        now = datetime.now()
        # HARD BLOCK
        if (pnl <= -self.stoploss and self.position_silver==0 and self.position_mini==0) or (self.position_silver==0 and self.position_mini==0 and now.hour >= 23 and now.minute >= 30):
            return
        
        l1 = self.market_data_engine.get_l1_snapshot()
        if l1 is None:
            return
        
        if self.params["panic"]==1:
            if self.position_silver!=0 and self.position_mini!=0:
                self._trigger_aggressive_sqoff(l1)
                self.params["panic"] = 0
                return
        
        if now.hour >= 23 and now.minute >= 30 and self.position_silver!=0 and self.position_mini!=0:
            self._trigger_aggressive_sqoff(l1)
            return
        
        if now.hour >= 23 and now.minute >= 20 and self.position_silver!=0 and self.position_mini!=0:
            # sirf tab trigger jab working order already nahi hai
            if self.state == "IN_POSITION" and self.timebasedSqoff is None:

                if self.position_silver == 1:
                    self._start_close("SELL", l1)
                    self.timebasedSqoff = "YES"
                    self.sqoff_mode = "PASSIVE"
                else:
                    self._start_close("BUY", l1)
                    self.timebasedSqoff = "YES"
                    self.sqoff_mode = "PASSIVE"

                return

        # --------------------------------------------------
        # IN_POSITION
        # same signal / None -> do nothing
        # opposite signal -> start close
        # --------------------------------------------------
        print(self.position_silver, self.position_mini, signal, self.state, self.executionSpread)
        if self.state == "IN_POSITION":

            if self.position_silver == 1 and self.position_mini == -6:
                if signal == "SELL":
                    self._start_close("SELL", l1)

                if pnl<=-self.stoploss and self.sqoff_mode is None:
                    self.sqoff_mode = "PASSIVE"
                    self.sqoff_trigger_pnl = pnl
                    self._start_close("SELL", l1)

                return

            if self.position_silver == -1 and self.position_mini == 6:
                if signal == "BUY":
                    self._start_close("BUY", l1)

                if pnl<=-self.stoploss and self.sqoff_mode is None:
                    self.sqoff_mode = "PASSIVE"
                    self.sqoff_trigger_pnl = pnl
                    self._start_close("BUY", l1)
                return

            return

        # --------------------------------------------------
        # WORKING
        # fill? hedge
        # signal dead/opposite? cancel, then maybe re-enter
        # same signal? modify
        # --------------------------------------------------
        if self.state == "WORKING":
            if self.sqoff_mode == "PASSIVE" and self.timebasedSqoff is None:
                improvement_level = self.sqoff_trigger_pnl + abs(self.sqoff_trigger_pnl) * self.stoploss_improvement_pct
                if pnl >= improvement_level:
                    self._cancel_passive()
                    self.sqoff_mode = None
                    self.sqoff_trigger_pnl = None
                    return

                aggressive_level = self.sqoff_trigger_pnl - abs(self.sqoff_trigger_pnl) * self.stoploss_aggressive_pct
                if pnl <= aggressive_level:
                    self._trigger_aggressive_sqoff(l1)
                    return

            filled = self._check_passive_fill_and_hedge()
            if filled:
                return

            if (signal is None or signal != self.side) and self.sqoff_mode is None:
                self._cancel_passive()

                # after cancel:
                # if we are flat (IDLE) and signal is valid, place fresh order
                if self.state == "IDLE":
                    if signal == "BUY" and abs(self.position_silver) < self.position_limit:
                        self._place_passive_buy(l1)
                    elif signal == "SELL" and abs(self.position_silver) < self.position_limit:
                        self._place_passive_sell(l1)

                return

            self._modify_passive_to_l1(l1)
            return

        # --------------------------------------------------
        # IDLE
        # fresh entry
        # --------------------------------------------------
        if self.state == "IDLE":

            if signal == "BUY" and abs(self.position_silver) < self.position_limit:
                self._place_passive_buy(l1)
                return

            if signal == "SELL" and abs(self.position_silver) < self.position_limit:
                self._place_passive_sell(l1)
                return
            
    # ======================================================
    # AGGRESSIVE SQOFF
    # ======================================================
    def _trigger_aggressive_sqoff(self, l1):
        t1 = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open('spreadTrades.txt', 'a') as f:
            f.write(f"{t1} Aggressive sqoff triggered\n")
        # 1) cancel existing passive
        if self.passive_order_id is not None:
            self._cancel_passive()

        if self.position_silver==0 and self.position_mini==0:
            return

        # 2) place silver aggressively (force fill)
        if self.position_silver == 1:
            self.side = "SELL"
            price = l1["silver_bid"] - sqoff_aggressiveness
            txn = self.kite.TRANSACTION_TYPE_SELL
        else:
            self.side = "BUY"
            price = l1["silver_ask"] + sqoff_aggressiveness
            txn = self.kite.TRANSACTION_TYPE_BUY

        self.mode = "CLOSE"

        self.passive_order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange="MCX",
            tradingsymbol=silver_symbol,
            transaction_type=txn,
            quantity=1,
            product=self.kite.PRODUCT_MIS,
            order_type=self.kite.ORDER_TYPE_LIMIT,
            price=price
        )

        self.state = "WORKING"
        self.passive_price = price

        # 3) immediately check fill
        filled = self._check_passive_fill_and_hedge()

        # 4) agar kisi reason se fill detect nahi hua, force hedge
        if not filled:
            self._hedge_mini()
            self.position_silver = 0
            self.position_mini = 0
            self.state = "IDLE"
            self._clear_working_order()

        # 5) reset sqoff flags
        self.sqoff_mode = None
        self.sqoff_trigger_pnl = None
        self.timebasedSqoff = None

        print("AGGRESSIVE SQOFF DONE", flush=True)
    # ======================================================
    # ENTRY HELPERS
    # ======================================================

    def _place_passive_buy(self, l1):

        price = l1["silver_bid"] + aggression

        self.passive_order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange="MCX",
            tradingsymbol=silver_symbol,
            transaction_type=self.kite.TRANSACTION_TYPE_BUY,
            quantity=1,
            product=self.kite.PRODUCT_MIS,
            order_type=self.kite.ORDER_TYPE_LIMIT,
            price=price
        )

        self.state = "WORKING"
        self.side = "BUY"
        self.mode = "OPEN"
        self.passive_price = price

    def _place_passive_sell(self, l1):

        price = l1["silver_ask"] - aggression

        self.passive_order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange="MCX",
            tradingsymbol=silver_symbol,
            transaction_type=self.kite.TRANSACTION_TYPE_SELL,
            quantity=1,
            product=self.kite.PRODUCT_MIS,
            order_type=self.kite.ORDER_TYPE_LIMIT,
            price=price
        )

        self.state = "WORKING"
        self.side = "SELL"
        self.mode = "OPEN"
        self.passive_price = price

    # ======================================================
    # CLOSE HELPER
    # ======================================================

    def _start_close(self, side, l1):

        self.mode = "CLOSE"
        self.side = side

        if side == "BUY":
            price = l1["silver_bid"] + aggression
            txn = self.kite.TRANSACTION_TYPE_BUY
        else:
            price = l1["silver_ask"] - aggression
            txn = self.kite.TRANSACTION_TYPE_SELL

        self.passive_order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange="MCX",
            tradingsymbol=silver_symbol,
            transaction_type=txn,
            quantity=1,
            product=self.kite.PRODUCT_MIS,
            order_type=self.kite.ORDER_TYPE_LIMIT,
            price=price
        )

        self.state = "WORKING"
        self.passive_price = price

    # ======================================================
    # PASSIVE SILVER MANAGEMENT
    # ======================================================

    def _modify_passive_to_l1(self, l1):

        if self.passive_order_id is None:
            return

        if self.side == "BUY":
            new_price = l1["silver_bid"] + aggression
        else:
            new_price = l1["silver_ask"] - aggression

        if new_price == self.passive_price:
            return

        try:
            self.kite.modify_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=self.passive_order_id,
                price=new_price
            )
            self.passive_price = new_price
        except Exception as e:
            print("modify failed:", e, flush=True)

    def _check_passive_fill_and_hedge(self):

        if self.passive_order_id is None:
            return False

        latest = self._latest_order(self.passive_order_id)
        filled_qty = int(latest["filled_quantity"])

        if filled_qty == 0:
            return False
        
        self.silverExecutionPrice = float(latest['average_price'])/(np.exp(0.055*silver_days/365.25))

        self.silverMiniExecutionPrice = self._hedge_mini()/(np.exp(0.055*mini_days/365.25))

        print("Execution prices are ", self.silverExecutionPrice, self.silverMiniExecutionPrice)

        t1 = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if self.mode == "OPEN":
            self.executionSpread = 1e4*(self.silverExecutionPrice - self.silverMiniExecutionPrice)/(0.5*(self.silverExecutionPrice + self.silverMiniExecutionPrice))
            if self.side == "BUY":
                self.position_silver = 1
                self.position_mini = -6

                with open('spreadTrades.txt', 'a') as f:
                    f.write(f"{t1} Bought the spread at {self.executionSpread}\n")
            else:
                self.position_silver = -1
                self.position_mini = 6

                with open('spreadTrades.txt', 'a') as f:
                    f.write(f"{t1} Sold the spread at {self.executionSpread}\n")

            self.state = "IN_POSITION"

        elif self.mode == "CLOSE":
            self.executionSpread = 1e4*(self.silverExecutionPrice - self.silverMiniExecutionPrice)/(0.5*(self.silverExecutionPrice + self.silverMiniExecutionPrice))
            self.position_silver = 0
            self.position_mini = 0
            self.state = "IDLE"

            with open('spreadTrades.txt', 'a') as f:
                    f.write(f"{t1} Closed the spread at {self.executionSpread}\n")

        # self._clear_working_order()
        return True

    def _cancel_passive(self):

        if self.passive_order_id is None:
            return

        order_id = self.passive_order_id
        current_mode = self.mode
        current_side = self.side

        try:
            self.kite.cancel_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order_id
            )
        except Exception:
            pass

        latest = self._latest_order(order_id)
        filled_qty = int(latest["filled_quantity"])

        # cancel race: fill happened before cancel completed
        if filled_qty > 0:
            self.silverExecutionPrice = float(latest['average_price'])/(np.exp(0.055*silver_days/365.25))

            self.silverMiniExecutionPrice = self._hedge_mini()/(np.exp(0.055*mini_days/365.25))

            t1 = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            if current_mode == "OPEN":
                self.executionSpread = 1e4*(self.silverExecutionPrice - self.silverMiniExecutionPrice)/(0.5*(self.silverExecutionPrice + self.silverMiniExecutionPrice))
                if current_side == "BUY":
                    self.position_silver = 1
                    self.position_mini = -6

                    with open('spreadTrades.txt', 'a') as f:
                        f.write(f"{t1} Bought the spread at {self.executionSpread}\n")

                else:
                    self.position_silver = -1
                    self.position_mini = 6

                    with open('spreadTrades.txt', 'a') as f:
                        f.write(f"{t1} Sold the spread at {self.executionSpread}\n")
                self.state = "IN_POSITION"

            elif current_mode == "CLOSE":
                self.position_silver = 0
                self.position_mini = 0
                self.state = "IDLE"

                with open('spreadTrades.txt', 'a') as f:
                        f.write(f"{t1} Closed the spread at {self.executionSpread}\n")

        else:
            # no fill happened
            if current_mode == "OPEN":
                self.state = "IDLE"
            elif current_mode == "CLOSE":
                self.state = "IN_POSITION"
                if self.sqoff_mode == "PASSIVE":
                    self.sqoff_mode = None

        # self._clear_working_order()

    # ======================================================
    # ACTIVE MINI HEDGE
    # ======================================================

    def _hedge_mini(self):

        remaining = mini_lot

        if self.side == "BUY":
            hedge_side = self.kite.TRANSACTION_TYPE_SELL
        else:
            hedge_side = self.kite.TRANSACTION_TYPE_BUY

        totalExecutionValue = 0 
        while remaining > 0:

            l1 = self.market_data_engine.get_l1_snapshot()
            if l1 is None:
                time.sleep(hedge_sleep_duration)
                continue

            if hedge_side == self.kite.TRANSACTION_TYPE_SELL:
                hedge_price = l1["mini_bid"] - self.ioc_width
            else:
                hedge_price = l1["mini_ask"] + self.ioc_width

            hedge_order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange="MCX",
                tradingsymbol=mini_symbol,
                transaction_type=hedge_side,
                quantity=remaining,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=hedge_price,
                validity=self.kite.VALIDITY_IOC
            )

            latest = self._latest_order(hedge_order_id)
            filled = int(latest["filled_quantity"])
            remaining -= filled

            if filled == 0:
                time.sleep(hedge_sleep_duration)

            totalExecutionValue = totalExecutionValue + filled*float(latest['average_price'])

        if totalExecutionValue!=0 and remaining==0:
            return totalExecutionValue/mini_lot

    # ======================================================
    # UTILITIES
    # ======================================================

    def _clear_working_order(self):

        self.passive_order_id = None
        self.passive_price = None
        self.side = None
        self.mode = None
        self.sqoff_mode = None
        self.sqoff_trigger_pnl = None
        self.timebasedSqoff = None
        self.silverExecutionPrice = 0 
        self.silverMiniExecutionPrice = 0 
        self.executionSpread = None

    def _latest_order(self, order_id):

        history = self.kite.order_history(order_id)
        return history[-1]