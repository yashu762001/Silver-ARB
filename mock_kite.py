# mock_kite.py
import random
import config


class MockKiteConnect:
    def __init__(self, api_key=None):
        self.api_key = api_key

        self.TRANSACTION_TYPE_BUY = "BUY"
        self.TRANSACTION_TYPE_SELL = "SELL"
        self.VARIETY_REGULAR = "regular"
        self.PRODUCT_MIS = "MIS"
        self.ORDER_TYPE_LIMIT = "LIMIT"
        self.VALIDITY_IOC = "IOC"

        self.orders = {}
        self.next_order_id = 10001

        self.current_price = {
            config.SILVER_TRADINGSYMBOL: 90000.0,
            config.SILVER_MINI_TRADINGSYMBOL: 89950.0,
        }

        self.position_qty = {
            config.SILVER_TRADINGSYMBOL: 0,
            config.SILVER_MINI_TRADINGSYMBOL: 0,
        }

        self.avg_price = {
            config.SILVER_TRADINGSYMBOL: 0.0,
            config.SILVER_MINI_TRADINGSYMBOL: 0.0,
        }

        random.seed(42)

        self.silver_sequence = []
        self.mini_sequence = []

        silver = 90000
        mini = 89950

        for _ in range(10000):
            silver += random.randint(-8, 8)
            mini += random.randint(-8, 8)

            if abs(silver - mini) > 120:
                mini += int((silver - mini) * 0.30)

            self.silver_sequence.append(float(silver))
            self.mini_sequence.append(float(mini))

        self.step = 0

    def set_access_token(self, token):
        pass

    def place_order(self, **kwargs):
        order_id = str(self.next_order_id)
        self.next_order_id += 1

        order = {
            "order_id": order_id,
            "status": "OPEN",
            "filled_quantity": 0,
            "average_price": 0.0,
            "quantity": int(kwargs.get("quantity", 0)),
            "price": float(kwargs.get("price", 0.0)),
            **kwargs,
        }

        self.orders[order_id] = order

        print(
            f"[MOCK KITE] PLACED -> "
            f"{order['tradingsymbol']} "
            f"{order['transaction_type']} "
            f"qty={order['quantity']} "
            f"price={order['price']} "
            f"validity={order.get('validity', 'DAY')}",
            flush=True
        )

        if order.get("validity") == self.VALIDITY_IOC:
            self._fill_order(order_id, force=True)

        return order_id

    def modify_order(self, **kwargs):
        order_id = kwargs.get("order_id")

        if order_id not in self.orders:
            return order_id

        order = self.orders[order_id]

        if order["status"] != "OPEN":
            return order_id

        if "price" in kwargs:
            order["price"] = float(kwargs["price"])

        if "quantity" in kwargs:
            order["quantity"] = int(kwargs["quantity"])

        print(
            f"[MOCK KITE] MODIFIED -> {order_id} "
            f"price={order['price']} qty={order['quantity']}",
            flush=True
        )

        return order_id

    def cancel_order(self, variety, order_id):
        if order_id in self.orders:
            if self.orders[order_id]["status"] == "OPEN":
                self.orders[order_id]["status"] = "CANCELLED"
                print(f"[MOCK KITE] CANCELLED -> {order_id}", flush=True)

        return order_id

    def order_history(self, order_id):
        if order_id not in self.orders:
            return [{
                "status": "UNKNOWN",
                "filled_quantity": 0,
                "average_price": 0.0,
            }]

        self._fill_order(order_id)
        return [self.orders[order_id].copy()]

    def quote(self, symbol):
        if self.step < len(self.silver_sequence):
            silver_mid = self.silver_sequence[self.step]
            mini_mid = self.mini_sequence[self.step]
        else:
            silver_mid = self.silver_sequence[-1]
            mini_mid = self.mini_sequence[-1]

        # IMPORTANT: update current_price here
        self.current_price[config.SILVER_TRADINGSYMBOL] = silver_mid
        self.current_price[config.SILVER_MINI_TRADINGSYMBOL] = mini_mid

        self.step += 1

        if symbol == config.SILVER_TRADINGSYMBOL:
            ltp = silver_mid
        else:
            ltp = mini_mid

        return {
            symbol: {
                "last_price": ltp,
                "depth": {
                    "buy": [{"price": round(ltp - 2, 1)}],
                    "sell": [{"price": round(ltp + 2, 1)}]
                }
            }
        }

    def positions(self):
        net = []

        for symbol in [
            config.SILVER_TRADINGSYMBOL,
            config.SILVER_MINI_TRADINGSYMBOL,
        ]:
            qty = self.position_qty[symbol]
            avg = self.avg_price[symbol]
            ltp = self.current_price[symbol]

            pnl = qty * (ltp - avg)

            net.append({
                "tradingsymbol": symbol,
                "quantity": qty,
                "average_price": avg,
                "last_price": ltp,
                "pnl": pnl,
            })

        return {"net": net}

    def _fill_order(self, order_id, force=False):
        order = self.orders[order_id]

        if order["status"] != "OPEN":
            return

        symbol = order["tradingsymbol"]
        side = order["transaction_type"]
        price = float(order["price"])
        qty = int(order["quantity"])
        filled = int(order["filled_quantity"])
        remaining = qty - filled

        if remaining <= 0:
            return

        ltp = self.current_price.get(symbol, price)
        bid = ltp - 2
        ask = ltp + 2

        if side == self.TRANSACTION_TYPE_BUY and price >= ask:
            fill_price = ask

        elif side == self.TRANSACTION_TYPE_SELL and price <= bid:
            fill_price = bid

        elif force:
            fill_price = ask if side == self.TRANSACTION_TYPE_BUY else bid

        else:
            return

        fill_qty = remaining

        order["filled_quantity"] += fill_qty
        order["average_price"] = fill_price
        order["status"] = "COMPLETE"

        signed_qty = fill_qty if side == self.TRANSACTION_TYPE_BUY else -fill_qty
        self._update_position(symbol, signed_qty, fill_price)

        print(
            f"[MOCK KITE] FILLED -> "
            f"{symbol} {side} qty={fill_qty} price={fill_price}",
            flush=True
        )

    def _update_position(self, symbol, signed_qty, price):
        old_qty = self.position_qty[symbol]
        old_avg = self.avg_price[symbol]

        new_qty = old_qty + signed_qty

        if old_qty == 0:
            new_avg = price

        elif old_qty * signed_qty > 0:
            new_avg = (
                abs(old_qty) * old_avg + abs(signed_qty) * price
            ) / abs(new_qty)

        elif new_qty == 0:
            new_avg = 0.0

        else:
            new_avg = price

        self.position_qty[symbol] = new_qty
        self.avg_price[symbol] = new_avg