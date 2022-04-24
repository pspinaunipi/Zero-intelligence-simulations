import santa_fe_4
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
from fbm import fgn
import scipy.stats


def generate_order(arr, df, s , loc, lenght):
    sign = santa_fe_4.rand_sign()

    if sign == 1:
        best_price = np.where(arr > 0)[0][-1]
        opposite = np.where(arr < 0)[0][0]
        pos = -8
        while pos <= 0:
            pos = np.random.standard_t(df) * s + loc + best_price
        if pos >= opposite:
            pos = opposite

    else:

        best_price = np.where(arr < 0)[0][0]
        opposite = np.where(arr > 0)[0][-1]
        pos = 10e10
        while pos >= lenght - 0.5:
            pos = best_price - np.random.standard_t(df) * s - loc
        if pos <= opposite:
            pos  = opposite


    return int(pos + 0.5), sign


def cancel_order(arr):
    tot = np.abs(arr).sum()
    pos = np.random.randint(tot)
    pos_orders = np.abs(arr).cumsum()
    price =  np.where(pos_orders > pos)[0][0]
    if arr[price] > 0:
        sign = -1
    else:
        sign = 1
    return price, sign

def do_market_order(arr, sign):

    if sign == 1:
        pos  = np.where(arr < 0)[0][0]
    else:
        pos = np.where(arr > 0)[0][-1]

    return pos


def do_cancel_order(arr, mid_p, sign):

    n_orders_bid = arr[arr > 0].sum()
    n_orders_ask = -(arr[arr < 0].sum())

    if sign == 1:
        pos = np.random.randint(n_orders_bid)
    else:
        pos = np.random.randint(n_orders_bid , n_orders_ask + n_orders_bid)

    pos_orders = np.abs(arr).cumsum()

    price =  np.where(pos_orders > pos)[0][0]

    return price

def do_limit_order(arr, df, s , ll, lenght, sign):

    if sign == 1:
        best_price = np.where(arr > 0)[0][-1]
        opposite = np.where(arr < 0)[0][0]
        pos = -8
        while pos <= 0 or pos >= opposite:
            pos = int(scipy.stats.t.rvs(df, loc = ll, scale = s) + best_price + 0.5)

    else:
        best_price = np.where(arr < 0)[0][0]
        opposite = np.where(arr > 0)[0][-1]
        pos = 10e10
        while pos >= lenght or pos <= opposite:
            pos = int(best_price - scipy.stats.t.rvs(df, loc = ll , scale = s) + 0.5)


    return pos


def sim_LOB(l_rate, m_rate, c_rate, k, iterations, df = 1.10, scale = 42, loc = -16, h_exp = 0.6):

    #initialize LOB
    lob = np.ones(k, dtype = np.int16)
    lob[k//2:] = -1
    #cumpute sign using fractional gaussian noise
    arr_sign = np.sign(fgn(n = int(iterations * 1.2), hurst = h_exp, length = 1, method = 'daviesharte'))

    spr = np.zeros(int(iterations * 1.2))
    mid_price = np.zeros(int(iterations * 1.2))
    arr_shift = np.zeros(int(iterations * 1.2))
    arr_type = np.zeros(int(iterations * 1.2))
    tot_orders = np.zeros(int(iterations * 1.2))
    #compute inter arrival times
    next_order = santa_fe_4.inter_arrival(l_rate + m_rate + c_rate * np.abs(lob).sum())

    for i in range(int(iterations * 1.2)):
        bid_size = lob[lob > 0].sum()
        ask_size = -lob[lob < 0].sum()

        sign = arr_sign[i]

        tot = l_rate + m_rate + c_rate * np.abs(lob).sum()
        # find type next order

        FLAG = False
        while FLAG is False:
            o_type = np.random.choice([0,1,2], p = [l_rate / tot, m_rate / tot, c_rate * np.abs(lob).sum() / tot])

            # do not cancel the last quote
            if bid_size > 1 and ask_size > 1:
                FLAG = True

            elif bid_size == 1 and sign == 1 and o_type == 2:
                FLAG= False

            elif bid_size == 1 and sign == -1 and o_type == 1:
                FLAG= False

            elif ask_size == 1 and  sign == -1 and o_type == 2:
                FLAG= False

            elif ask_size == 1 and sign == 1 and o_type == 1:
                FLAG= False

            else:
                FLAG = True

        mp = santa_fe_4.find_mid_price(lob)

        if o_type == 0:
            price = do_limit_order(lob, df, scale, loc, k, sign)

        elif o_type == 1:
            price = do_market_order(lob, sign)

        else:
            price = do_cancel_order(lob, mp, sign)
            sign = - sign


        lob[price] += sign
        spr[i] = santa_fe_4.find_spread(lob)
        new_mp = santa_fe_4.find_mid_price(lob)
        mid_price[i] = new_mp
        arr_type[i] = o_type
        tot_orders[i] = np.abs(lob).sum()

        shift = int(new_mp - k//2)
        arr_shift[i] = shift

        #center LOB around mid price
        if shift > 0:
            lob[:-shift] = lob[shift:]
            lob[-shift:] = np.zeros(len(lob[-shift:]))
        elif shift < 0:
            lob[-shift:] = lob[:shift]
            lob[:-shift] = np.zeros(len(lob[:-shift]))

    price = arr_shift.cumsum() + mid_price

    return lob[-iterations:], spr[-iterations:], price[-iterations:], arr_type[-iterations:]

@njit()
def MF_sim(l_rate, m_rate, c_rate, k, iterations, df = 1.10, scale = 42):

    #initialize LOB
    lob = np.ones(k, dtype = np.int16)
    lob[k//2:] = -1

    spr = np.zeros(iterations)
    mid_price = np.zeros(iterations)
    i = 0

    while i < iterations:

        price, sign = generate_order(lob, df, scale, -16, k)

        lob[price] += sign
        spr[i] = santa_fe_4.find_spread(lob)
        new_mp = santa_fe_4.find_mid_price(lob)
        mid_price[i] = new_mp
        i += 1

        tot = np.abs(lob).sum()
        bb = len(np.where(lob > 0)[0])
        oo = len(np.where(lob < 0)[0])

        j = np.random.binomial(tot, c_rate)

        while j > 0 and bb > 2 and oo > 2 and i < iterations:
            price, sign = cancel_order(lob)
            lob[price] += sign
            spr[i] = santa_fe_4.find_spread(lob)
            new_mp = santa_fe_4.find_mid_price(lob)
            mid_price[i] = new_mp
            i += 1
            j -= 1
            bb = len(np.where(lob > 0)[0])
            oo = len(np.where(lob < 0)[0])
    return lob, spr, mid_price
