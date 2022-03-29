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
def do_limit_order(arr):

    pos = np.random.randint(len(arr))

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
def do_market_order(arr):
    sign = rand_sign()
    if  sign ==1:
        _, price = find_max_min(arr)

    else:
        price, _ = find_max_min(arr)

    return  price, sign

@njit()
def do_cancel_order(arr):
    i=0
    pos = -1
    tot = np.abs(arr).sum()
    xx = np.random.randint(tot)
    c_sum_arr = np.abs(arr).cumsum()

    while pos == -1:
        if xx <= c_sum_arr[i]:
            pos = i
        i +=1
    sign = sign_value(arr[pos])

    return pos, -sign

@njit()
def out_of_equilibrium_start(maximum, iterations):

    new_lob = np.zeros((iterations, maximum), dtype=np.int16)
    #initialize lob
    new_lob[0][0 : maximum // 2] = 1
    new_lob[0][maximum // 2 : maximum + 1] = -1

    return new_lob


@njit()
def update_c_times(lst_of_lst,value):
    for i,lst in enumerate(lst_of_lst):
        lst_of_lst[i] = update_times(lst, value)
    return lst_of_lst


@njit()
def find_n_cancel(arr_lob,delta):

    n_cancel = 0
    #find total number of orders
    tot = np.abs(arr_lob).sum()
    #find how many of those are cancelled
    '''
    for i in range(tot):
        prob = np.random.random()
        if delta < prob:
            n_cancel += 1
    '''
    n_cancel = np.random.poisson(delta*tot)
    return n_cancel

@njit()
def select_random(lst, probs):
    a = np.random.random()

    if a < probs[0]:
        value = 0
    elif probs[0] < a < probs[0] + probs[1]:
        value = 1
    else:
        value = 2

    return value


@njit()
def simulate_lob(limit_rate, market_rate, cancel_rate, max_val, iterations=10000):
    #initialize lob
    lob = out_of_equilibrium_start(max_val,iterations)

    orders = List()
    lst_sign = List()
    lst_price = List()
    lst_shift = List()

    i = 1
    while i < iterations:
        current_lob = lob[i-1][:]
        # find number of limit, market and cancel order in a unit of time
        n_limit = np.random.poisson(limit_rate * max_val)
        n_market = np.random.poisson(market_rate * 2)
        n_cancel = find_n_cancel(current_lob, cancel_rate)

        tot_orders = n_limit + n_market + n_cancel

        for _ in range(tot_orders):
            if i < iterations:
                current_lob = lob[i-1][:]
                # compute the probability that the next order is a market, cancel
                # or limit order
                prob_limit = n_limit / tot_orders
                prob_market = n_market / tot_orders
                prob_cancel = n_cancel / tot_orders

                o_type = select_random(List([0,1,2]), List([prob_limit, prob_market, prob_cancel]))
                #execute order and update lob
                if o_type == 0:
                    price, sign = do_limit_order(current_lob)
                    n_limit -= 1

                elif o_type == 1:
                    price, sign = do_market_order(current_lob)
                    n_market -= 1
                else:
                    price, sign = do_cancel_order(current_lob)
                    n_cancel -= 1

                tot_orders -= 1

                lob[i][:] = current_lob
                lob[i][price] += sign

                new_mp = find_mid_price(lob[i][:])
                shift = int(new_mp - max_val//2)

                if shift > 0:
                    lob[i][:-shift] = lob[i][shift:]
                    lob[i][-shift:] = np.zeros(len(lob[i][-shift:]))
                elif shift < 0:
                    lob[i][-shift:] = lob[i][:shift]
                    lob[i][:-shift] = np.zeros(len(lob[i][:-shift]))
                orders.append(o_type)
                lst_sign.append(sign)
                lst_price.append(price)
                lst_shift.append(shift)

                i += 1

    return  lob, orders, lst_sign, lst_price, lst_shift

@njit()
def find_second_best(array):
    best_bid = np.zeros(array.shape[0])
    best_ask = np.zeros(array.shape[0])
    for i in range(array.shape[0]):
        o = 0
        j = array.shape[1]
        while o < 2:
            if array[i,j] > 0:
                o += 1
            j -= 1

        best_bid[i] = j + 1

    for i in range(array.shape[0]):
        o = 0
        j = 0
        while o < 2:
            if array[i,j] < 0:
                o += 1
            j += 1

        best_ask[i] = j-1

    return best_bid, best_ask

@njit()
def find_best(array):
    lenght = len(array)
    best_bid = np.zeros(lenght)
    best_ask = np.zeros(lenght)
    for i in range(lenght):

        max_bid, min_ask = find_max_min(array[i,:])
        best_bid[i] = max_bid
        best_ask[i] = min_ask

    return best_bid, best_ask

@njit()
def find_gap(array):
    best_b, best_a = find_best(array)
    two_b, two_a = find_second_best(array)
    gap_b = (best_b-two_b).mean()
    gap_a = (two_a- best_a).mean()
    return (gap_a + gap_b) / 2

if __name__ == "__main__":

    rate_lim = 0.018
    rate_m   = 0.055
    rate_del = 0.107

    lob, order, typ, pric, shift  = simulate_lob(rate_lim, rate_m, rate_del,1000,200_000)

    md, sp = find_mid_spread_lob(lob)

    fig,ax = plt.subplots(1, 1, figsize = (10,7))
    plt.bar(np.arange(1000), lob[-1])
    plt.title("LOB order queue", fontsize =22 )
    plt.ylabel("# orders", fontsize = 18)
    plt.xlabel("price", fontsize = 18)
    plt.show()

    plt.plot(md[1:] + shift)
    plt.show()
    plt.plot(sp)
    plt.show()
    print(sp.mean())
    print(((md[1:] - md[:-1])**2).mean())
