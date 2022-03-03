from numba import njit
import numpy as np
import random


@njit()
def find_min(array):
    minimum = 1e10
    position = 0
    for i, element in enumerate(array):
        if element < minimum:
            minimum = element
            position = i

    return minimum, position

@njit()
def find_max(array):
    maximum = -1e10
    position = 0
    for i, element in enumerate(array):
        if element > maximum:
            maximum = element
            position = i

    return maximum, position

@njit()
def rand_sign():
    array = np.array([-1,1])
    return np.random.choice(array)

@njit()
def poisson_generator(rate):
    arrival_time = random.expovariate(rate)
    return arrival_time

@njit()
def out_of_equilibrium_start(min_value, max_value, tick_size):

    b_orders = []
    s_orders = []
    mid_value = (min_value + max_value) // 2

    for i in range(min_value, mid_value + tick_size, tick_size):
        b_orders.append(i)

    for i in range(b_orders[-1] + tick_size, max_value + tick_size, tick_size):
        s_orders.append(i)

    return b_orders, s_orders

@njit()
def initialize_list_times(tot, rate):

    array_times = []

    for i in range(tot):
        array_times.append(poisson_generator(rate))

    return array_times


@njit()
def next_order(time_limit, buy_c, sell_c, time_market):

    limit  = False
    cancel = False
    market = False

    min_l, pos_l = find_min(time_limit)

    min_bc, pos_bc = find_min(buy_c)
    min_sc, pos_sc = find_min(sell_c)

    lst_times = [min_l, min_bc, min_sc, time_market]

    min_time, order_type = find_min(lst_times)

    if order_type == 0:
        sign = 0
        limit = True
        pos = pos_l
        t_time =  min_l

    elif order_type == 1:

        cancel = True
        sign = +1
        pos = pos_bc
        t_time =  min_bc

    elif order_type == 2:

        cancel = True
        sign = -1
        pos = pos_sc
        t_time =  min_sc

    elif order_type == 3:

        market = True
        sign = rand_sign()
        pos = 0
        t_time =  time_market


    return t_time, pos, sign, limit, market, cancel

@njit()
def subtract_from_list(lst,value):
    if lst != None:
        for i, element in enumerate(lst):
            lst[i] = element - value
    return lst

@njit()
def find_best_prices(sign,lst):

    if sign == 1:
        _, pos = find_min(lst)
    else:
        _, pos = find_max(lst)

    return pos

@njit()
def find_sign_limit(buy_orders,sell_orders, prices, pos):

    mid_p = (find_max(buy_orders)[0] + find_min(sell_orders)[0]) / 2
    if prices[pos] < mid_p:
        sign = 1

    elif prices[pos] > mid_p:
        sign = -1

    else:
        sign = rand_sign()

    return sign

@njit()
def find_sign_cancel(buy_orders, prices, pos):

    price = prices[pos]
    if price in buy_orders:
        sign = 1
    else:
        sign = -1

    return sign

@njit()
def sim_zero_intelligent(rate_limit, old_rate_market,
                         rate_cancel, min_val, max_val, max_iterations = 5_000,
                         tick_size = 5, verbose = False):

    rate_market = old_rate_market * 2
    buy_orders, sell_orders = out_of_equilibrium_start(min_val, max_val, tick_size)

    lst_prices = buy_orders + sell_orders

    limit_time   = initialize_list_times(len(lst_prices), rate_limit)
    buy_cancel   = initialize_list_times(len(buy_orders), rate_cancel)
    sell_cancel  = initialize_list_times(len(sell_orders), rate_cancel)
    market_time  = poisson_generator(rate_market)

    buy_limit_counter   = 0
    sell_limit_counter  = 0
    buy_cancel_counter  = 0
    sell_cancel_counter = 0
    buy_market_counter  = 0
    sell_market_counter = 0

    max_buy_limit_counter  = 0
    min_sell_limit_counter = 0

    stats = dict()

    md = []
    sp = []

    for i in range(max_iterations):
        transaction_time, position, sign, Limit, Market, Cancel = next_order(
            limit_time, buy_cancel, sell_cancel, market_time)

        if Limit is True:
            sign = find_sign_limit(buy_orders,sell_orders, lst_prices, position)
            price = lst_prices[position]

            new_limit_time = poisson_generator(rate_limit)
            new_cancel_time = poisson_generator(rate_cancel)

            if sign == 1:
                if price >= find_max(buy_orders)[0]:
                    max_buy_limit_counter += 1

                buy_orders.append(price)
                buy_cancel.append(new_cancel_time + transaction_time)
                buy_limit_counter += 1



            else:
                if price <= find_min(sell_orders)[0]:
                    min_sell_limit_counter += 1
                sell_orders.append(price)
                sell_cancel.append(new_cancel_time + transaction_time)
                sell_limit_counter += 1

            limit_time[position] += new_limit_time


        elif Market is True:

            if sign == 1:
                position = find_best_prices(sign,sell_orders)
                buy_market_counter += 1
                del sell_orders[position]
                del sell_cancel[position]
            else:
                position = find_best_prices(sign,buy_orders)
                sell_market_counter += 1
                del buy_orders[position]
                del buy_cancel[position]

            market_time += poisson_generator(rate_market)

        elif Cancel is True:

            if sign == 1:
                buy_cancel_counter  += 1
                del buy_orders[position]
                del buy_cancel[position]
            else:
                sell_cancel_counter  += 1
                del sell_orders[position]
                del sell_cancel[position]

        limit_time   = subtract_from_list(limit_time, transaction_time)
        buy_cancel  = subtract_from_list(buy_cancel, transaction_time)
        sell_cancel = subtract_from_list(sell_cancel, transaction_time)

        market_time -= transaction_time

        mid_price = (find_max(buy_orders)[0] + find_min(sell_orders)[0]) / 2
        spread = - find_max(buy_orders)[0] + find_min(sell_orders)[0]

        md.append(mid_price)
        sp.append(spread)

        stats["buy limit orders"]   = buy_limit_counter
        stats["sell limit orders"]  = sell_limit_counter
        stats["buy cancel orders"]  = buy_cancel_counter
        stats["sell cancel orders"] = sell_cancel_counter
        stats["buy market orders"]  = buy_market_counter
        stats["sell market orders"] = sell_market_counter

        stats["best price buy limit order"]   = max_buy_limit_counter
        stats["best price sell limit order"]  = min_sell_limit_counter

    return md, sp, stats


def mean_lst(lst):
    a = 0
    for element in lst:
        a += element
    return a/len(lst)


if __name__ == "__main__":


    ask = [i for i in range(21_000,21_500)]
    bid = [i for i in range(21_500,22_000)]

    rate_lim = 1 * 500
    rate_m   = 5
    rate_del = 10


    sp,md = sim_zero_intelligent(ask, bid, rate_lim, rate_m,
                               rate_del, limit = 500, max_iterations = 100,
                               tick_size = 1)

    print(sp,md)
