import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import time

def poisson_generator(rate):
    arrival_time = random.expovariate(rate)
    return arrival_time

def check_sign(val):
    if val != -1 and val != 1:
        raise SystemExit("Error: Sign must be either 1 or -1")

    return val

def check_e_type(val):
    if val != 1 and val != 2:
        raise SystemExit("Error: Sign must be either 1 or -1")

    return val


class LimitOrder():

    def __init__(self, price, volume, time, sign, e_type):
        self.price  = price
        self.volume = volume
        self.time   = time
        self.sign   = check_sign(sign)
        self.e_type = check_e_type(e_type)


class MarketOrder():

    def __init__(self, volume, time, sign):
        self.time  = time
        self.volume = volume
        self.sign   = check_sign(sign)
        self.e_type = 4

class LimitOrderBook():

    def __init__(self):

        self.buy_orders  = []
        self.sell_orders = []
        self.history_buy_orders  = []
        self.history_sell_orders = []

        headers =["time", "event type", "order ID", "size", "price",
                    "direction", "best buy", "best sell"]
        self.events = pd.DataFrame([], columns = headers)

    def mid_price(self):
        return (max(self.buy_orders) + min(self.sell_orders)) / 2

    def spread(self):
        return (-max(self.buy_orders) + min(self.sell_orders))

    def __add_limit_order__(self,order,initialize = False):

        if initialize is False:
            headers =["time", "event type", "order ID", "size", "price",
                        "direction", "best buy", "best sell"]

            values = [order.time, order.e_type, 450, order.volume,
                        order.price, order.sign, max(self.buy_orders) ,min(self.sell_orders)]

            new_event = pd.DataFrame([values],columns=headers)
            self.events = pd.concat([self.events,new_event])

        if order.sign == 1:
            self.buy_orders.append(order.price)
            if initialize is False:
                self.history_buy_orders.append(self.buy_orders)
        else:
            self.sell_orders.append(order.price)
            if initialize is False:
                self.history_sell_orders.append(self.sell_orders)


    def __add_cancel_order__(self,order):

        headers =["time", "event type", "order ID", "size", "price",
                    "direction", "best buy", "best sell"]

        values = [order.time, order.e_type, 450, order.volume,
                    order.price, order.sign, max(self.buy_orders) ,min(self.sell_orders)]

        new_event = pd.DataFrame([values],columns=headers)
        self.events = pd.concat([self.events,new_event])

        if order.sign == 1:
            self.buy_orders.remove(order.price)
            self.history_buy_orders.append(self.buy_orders)
        else:
            self.sell_orders.remove(order.price)
            self.history_sell_orders.append(self.sell_orders)

    def __add_market_order__(self,order):

        if order.sign == 1:
            best_price = self.events[self.events["direction"] == -1]["price"].min()
        else:
            best_price = self.events[self.events["direction"] == 1]["price"].max()


        headers =["time", "event type", "order ID", "size", "price",
                    "direction", "best buy", "best sell"]

        values = [order.time, order.e_type, 450, order.volume,
                    best_price, order.sign, max(self.buy_orders) ,min(self.sell_orders)]

        new_event = pd.DataFrame([values],columns=headers)
        self.events = pd.concat([self.events,new_event])

        if order.sign == 1:
            self.sell_orders.remove(min(self.sell_orders))
            self.history_sell_orders.append(self.sell_orders)
        else:
            self.buy_orders.remove(max(self.buy_orders))
            self.history_buy_orders.append(self.buy_orders)

    def add_order(self, order, initialize = False):

        if order.e_type == 1:
            self.__add_limit_order__(order, initialize)
        if order.e_type == 2:
            self.__add_cancel_order__(order)
        if order.e_type == 4:
            self.__add_market_order__(order)

    def rng_limit_order(self, vol, time, limit, tick_size):


        sign = np.random.choice([-1,1])

        if sign == 1:
            possible_prices =  []
            mid = int(self.mid_price()*100)
            for i in range(mid - limit, mid, tick_size):
                possible_prices.append(i / 100)

        if sign == -1:
            possible_prices =  []
            mid = int(self.mid_price()*100)
            for i in range(mid, mid + limit, tick_size):
                possible_prices.append(i / 100)



        price = np.random.choice(possible_prices)

        return  LimitOrder(price, vol, time, sign, 1)

    def rng_market_order(self, vol, time):

        sign = np.random.choice([-1, 1])
        return  MarketOrder(vol, time, sign)

    def rng_cancel_order(self, vol, time):

        sign  = np.random.choice([-1, 1])

        if sign == 1:
            price = np.random.choice(self.buy_orders)
        else:
            price = np.random.choice(self.sell_orders)

        return  LimitOrder(price, vol, time, sign, 2)

    def randomize_lob(self, vol, iterations=1000, min_val = 4_000,
                        max_val = 6_000, bid_0 = 215, ask_0 = 220, tick_size = 5):

        order_1 = LimitOrder(bid_0, vol, 0, 1, 1)
        order_2 = LimitOrder(ask_0, vol, 1, -1, 1)

        self.add_order(order_1, initialize = True)
        self.add_order(order_2, initialize = True)

        for i in range(2, iterations):
            new_limit_order = self.rng_limit_order(vol, i, min_val, max_val, tick_size)
            self.add_order(new_limit_order, initialize = True)



    def sim_zero_intelligent(self, rate_limit, rate_market, rate_cancel,
                             limit = 600, max_iterations = 5_000,
                             tick_size = 5, volume = 1, initialize = False):

        next_limit_order  = poisson_generator(rate_limit)
        next_market_order = poisson_generator(rate_market)
        next_cancel_order = poisson_generator(rate_cancel)

        transaction_time  = min(next_cancel_order,next_market_order,next_limit_order)

        for i in range(max_iterations):
            percent_complete = int(i / max_iterations * 100)
            if i % (max_iterations // 10) == 0:
                print("", end=f"\r {percent_complete} % done...")

            if next_limit_order < next_market_order and next_limit_order < next_cancel_order:
                #execute limit order
                next_order = self.rng_limit_order(volume, transaction_time, limit, tick_size)
                self.add_order(next_order, initialize)
                transaction_time += next_limit_order
                #rescale times
                next_market_order -= next_limit_order
                next_cancel_order -= next_limit_order
                #generate time new limit order
                next_limit_order   = poisson_generator(rate_limit)

            elif next_market_order < next_limit_order and next_market_order < next_cancel_order:
                #execute market order
                next_order = self.rng_market_order(volume, transaction_time)
                self.add_order(next_order, initialize)
                transaction_time += next_market_order
                #rescale times
                next_limit_order  -= next_market_order
                next_cancel_order -= next_market_order
                #generate time new market order
                next_market_order  = poisson_generator(rate_market)

            elif next_cancel_order < next_limit_order and next_cancel_order < next_market_order:
                next_order = self.rng_cancel_order(volume, transaction_time)
                self.add_order(next_order, initialize)
                transaction_time += next_cancel_order
                #rescale times
                next_limit_order  -= next_cancel_order
                next_market_order -= next_cancel_order
                #generate time new market order
                next_cancel_order   = poisson_generator(rate_cancel)

    def status(self):
        print(f"Mid price = {self.mid_price():.2f}")
        print(f"Spread = {self.spread():.2f}")
        print("Number of limit orders = ",self.events[self.events["event type"]==1].shape[0])
        print("Number of cancellations = ",self.events[self.events["event type"]==2].shape[0])
        print("Number of market orders = ",self.events[self.events["event type"]==4].shape[0])
        print(f"Trading time = {(self.events.time.max())/60/60:.2f} h")
        print(f"Volume limit order  =", self.events[self.events["event type"]==1]["size"].sum())
        print(f"Volume market order  =", self.events[self.events["event type"]==2]["size"].sum())
        print(f"Volume cancellations  =", self.events[self.events["event type"]==4]["size"].sum())

    def spread_distribution(self,**kwargs):
        mean_spread = (-self.events["best buy"]+self.events["best sell"]).mean()
        print(f"<s> = {mean_spread:.2f}")
        ((-self.events["best buy"]+self.events["best sell"]) / mean_spread).hist(**kwargs)
        plt.show()

    def stats(self):
        self.events["spread"] = -self.events["best buy"]+self.events["best sell"]
        self.events["mid price"] = (self.events["best buy"]+self.events["best sell"])/2
        print(self.events.agg(
                    {
                        "best buy": ["min", "max", "mean","std"],
                        "best sell": ["min", "max", "mean","std"],
                        "spread": ["min", "max", "mean","std"],
                        "mid price": ["min", "max", "mean","std"],
                    }).round(2))




    def out_of_equilibrium_start(self, vol, min_val = 4_000,
                                    max_val = 6_000, tick_size = 5):

        half_point = int((max_val + min_val) / 2)

        for i in range(min_val, half_point, tick_size):
            price = i / 100
            initial_order = LimitOrder(price, vol, 1, 1, 1)
            self.add_order(initial_order, initialize = True)

        for i in range (half_point, max_val, tick_size):
            price = i / 100
            initial_order = LimitOrder(price, vol, 1, -1, 1)
            self.add_order(initial_order, initialize = True)

if __name__=="__main__":
    lob = LimitOrderBook()
    lob.out_of_equilibrium_start(10, min_val = 21_000, max_val = 22_000, tick_size = 1)

    lim = 500
    mu = 5
    al = 1 * lim
    delta = 10

    start = time.time()
    #start simulations
    lob.sim_zero_intelligent(al ,mu, delta, max_iterations = 100_000, limit=lim,
                             tick_size = 1, volume = 10, initialize = False)
    finish = time.time()

    print(f"Time to finish ",int(finish-start), " sec")


    lob.status()
    lob.spread_distribution(bins=30,range = (0,4))

    lob.stats()
    plt.plot(lob.events["mid price"].to_numpy())
    plt.show()
