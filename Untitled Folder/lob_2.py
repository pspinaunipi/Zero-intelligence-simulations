def check_sign(val):
    if val != -1 and val != 1:
        raise SystemExit("Error: Sign must be either 1 or -1")

    return val

class LimitOrder():

    def __init__(self, price,sign):
        self.price  = price
        self.sign   = check_sign(sign)


class MarketOrder():

    def __init__(self, volume, time, sign):
        self.sign   = check_sign(sign)


class LimitOrderBook():

    def __init__(self):
        self.buy_orders  = []
        self.sell_orders = []

    def add_limit_order(self,limit_order):

        if limit_order.sign == 1:
            buy_orders.append(limit_order.price)
        else:
            sell_orders.append(limit_order.price)

    def mid_price(self):
        return (max(self.buy_orders) + min(self.sell_orders)) / 2

    def spread(self):
        return max(self.buy_orders) - min(self.sell_orders)

    def add_market_order(self,market_order):

        if market_order.sign == 1:
            buy_orders.remove(max(self.sell_orders))
        else:
            sell_orders.remove(min(self.buy_orders))
