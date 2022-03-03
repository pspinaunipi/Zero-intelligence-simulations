import numpy as np
from numba import njit
import random
import matplotlib.pyplot as plt
import time
from numba.typed import List

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
def sign_value(val):

    if val > 0:
        sign = int(1)
    elif val < 0:
        sign = int(-1)
    else:
        sign = int(0)

    return sign

@njit()
def rand_sign():
    array = np.array([-1,1])
    return int(np.random.choice(array))

@njit()
def poisson_generator(rate):
    arrival_time = random.expovariate(rate)
    return arrival_time

@njit()
def find_max_min(arr):
    lenght = len(arr)
    for i in range(lenght):
        if arr[i] > 0:
            max_buy = i

        if arr[-(i+1)] < 0:
            min_sell = lenght - (i+1)

    if min_sell == 0:
        min_sell = len(arr) + 1

    return max_buy, min_sell

@njit()
def find_mid_price(arr):
    max_bid, min_ask = find_max_min(arr)
    return (min_ask + max_bid) / 2

@njit()
def find_mid_spread(arr):
    max_bid, min_ask = find_max_min(arr)
    mid = (min_ask + max_bid) / 2
    spr = (min_ask - max_bid)
    return mid, spr

@njit()
def find_mid_spread_lob(lob_history):
    lenght = len(lob_history)

    spr = np.zeros(lenght)
    mid = np.zeros(lenght)

    for i,arr in enumerate(lob_history):
        current_mid, current_spr = find_mid_spread(arr)
        spr[i] = current_spr
        mid[i] = current_mid

    return mid, spr

@njit()
def do_limit_order(arr, pos):

    if arr[pos] != 0:
        sign = sign_value(arr[pos])

    else:
        mid_price = find_mid_price(arr)

        if pos < mid_price:
            sign = int(1)
        elif pos > mid_price:
            sign = int(-1)
        else:
            sign = rand_sign()

    return pos, sign

@njit()
def do_market_order(arr, sign_position):

    if  sign_position == 0:
        sign = 1
        _, price = find_max_min(arr)

    else:
        sign = -1
        price, _ = find_max_min(arr)

    return  price, sign

@njit()
def do_cancel_order(arr,pos):

    pos, sign = do_limit_order(arr, pos)

    return pos, -sign

@njit()
def out_of_equilibrium_start(maximum, iterations):

    new_lob = np.zeros((iterations, maximum), dtype=np.int16)
    #initialize lob
    new_lob[0][0 : maximum // 2] = 1
    new_lob[0][maximum // 2 : maximum + 1] = -1

    return new_lob


@njit()
def initialize_array_times(maximum, rate):

    array_times = List()

    for i in range(maximum):
        array_times.append(poisson_generator(rate))

    return array_times

@njit()
def initialize_cancel_times(maximum, rate):

    array_times = List()

    for i in range(maximum):
        array_times.append(List(List([poisson_generator(rate)])))

    return array_times

@njit()
def find_min_queue(lst_of_lst):
    position = 0
    min_value = 10e9

    for i,lst in enumerate(lst_of_lst):
        # for each list find minumum
        temp_min, temp_pos = find_min(lst)

        if temp_min < min_value:
            min_value = temp_min
            position = i

    return min_value, position

@njit()
def add_order_decay(lst, pos, t_arrival):
    lst[pos].append(t_arrival)


@njit()
def find_best_time(limit_lst, market_lst, cancel_lst):
    #find the nearest limit, market and cancel orders
    time_limit, next_limit = find_min(limit_lst)
    time_market, next_market = find_min(market_lst)
    time_cancel, next_cancel = find_min_queue(cancel_lst)
    #find the nearest order between them
    min_time, order_type = find_min([time_limit, time_market, time_cancel])

    return min_time, order_type

@njit()
def update_times(lst,value):
    for i, element in enumerate(lst):
        lst[i] = element - value
    return lst

@njit()
def update_c_times(lst_of_lst,value):
    for i,lst in enumerate(lst_of_lst):
        lst_of_lst[i] = update_times(lst, value)
    return lst_of_lst


@njit()
def execute_order(limit_lst, market_lst, cancel_lst, arr_lob,
                    limit_rate, market_rate, cancel_rate):

    #find the nearest limit, market and cancel orders
    time_limit, next_limit = find_min(limit_lst)
    time_market, next_market = find_min(market_lst)
    time_cancel, next_cancel = find_min_queue(cancel_lst)
    #find the nearest order between them

    min_time, order_type = find_min(List([time_limit, time_market, time_cancel]))

    #update queue time
    limit_lst  = update_times(limit_lst, min_time)
    market_lst = update_times(market_lst, min_time)
    cancel_lst = update_c_times(cancel_lst, min_time)

    if order_type == 0:
        #execute limit order
        price, sign = do_limit_order(arr_lob, next_limit)
        new_limit_arrival  = poisson_generator(limit_rate)
        new_cancel_arrival = poisson_generator(cancel_rate)
        #update limit and cancel queue
        limit_lst[next_limit] = new_limit_arrival
        add_order_decay(cancel_lst, price, new_cancel_arrival)
        o_type = "limit"

    elif order_type == 1:
        #execute market order
        price, sign = do_market_order(arr_lob, next_market)
        if price != 0 and price != len(arr_lob) + 1 :
            market_lst[next_market] = poisson_generator(market_rate)
            #update cancel queue
            del[cancel_lst[price][0]]
            o_type = "market"
        else:
            o_type = "none"
            market_lst[next_market] = poisson_generator(market_rate)

    elif order_type == 2:
        #execute cancel order
        price, sign = do_cancel_order(arr_lob, next_cancel)
        #update cancel queue
        del[cancel_lst[price][0]]
        o_type = "cancel"

    return  price, sign, o_type, limit_lst, market_lst, cancel_lst

@njit
def simulate_lob(limit_rate, market_rate, cancel_rate, max_val, iterations=10000):
    #initialize lob
    lob = out_of_equilibrium_start(max_val,iterations)

    orders = List()
    lst_sign = List()
    lst_price = List()

    #initialize array_times for limit and market order
    limit_times  = initialize_array_times(max_val, limit_rate)
    market_times = initialize_array_times(2, market_rate)
    cancel_times = initialize_cancel_times(max_val, cancel_rate)
    order_type = "none"

    for i in range(1,iterations):
        current_lob = lob[i-1][:]
        while order_type == "none":
            price, sign, order_type, limit_times, market_times, cancel_times = execute_order(
            limit_times, market_times, cancel_times, current_lob, limit_rate, market_rate, cancel_rate)

        lob[i][:] = current_lob
        lob[i][price] += sign
        orders.append(order_type)
        lst_sign.append(sign)
        lst_price.append(price)
        order_type = "none"

    return  lob, orders, lst_sign, lst_price

if __name__ == "__main__":

    lob,time,o,b,c = simulate_lob(1, 2, 300, 10 , 10)

    print(lob[-1][:])
    print(time)
