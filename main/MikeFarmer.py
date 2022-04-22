import santa_fe_4
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
from fbm import fgn


@njit()
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

@njit()
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
@njit()
def do_limit_order(arr, df, s , loc, lenght):
    sign = santa_fe_4.rand_sign()

    if sign == 1:
        best_price = np.where(arr > 0)[0][-1]
        opposite = np.where(arr < 0)[0][0]
        pos = -8
        while pos <= 0 or pos >= opposite:
            pos = np.random.standard_t(df) * s + loc + best_price
    else:

        best_price = np.where(arr < 0)[0][0]
        opposite = np.where(arr > 0)[0][-1]
        pos = 10e10
        while pos >= lenght - 0.5 or pos <= opposite:
            pos = best_price - np.random.standard_t(df) * s - loc


    return int(pos + 0.5), sign

@njit()
def sim_LOB(l_rate, m_rate, c_rate, k, iterations, df = 1.10, scale = 42, loc = -16):

    #initialize LOB
    lob = np.ones(k, dtype = np.int16)
    lob[k//2:] = -1

    spr = np.zeros(iterations)
    mid_price = np.zeros(iterations)
    arr_shift = np.zeros(iterations)

    #compute inter arrival times
    time_l = santa_fe_4.inter_arrival(l_rate * k)
    time_m = santa_fe_4.inter_arrival(m_rate * 2)
    time_c = santa_fe_4.inter_arrival(c_rate * np.abs(lob).sum())
    times = np.array([time_l, time_m, time_c])

    for i in range(iterations):
        # find type next order
        o_type = np.argmin(times)
        mp = santa_fe_4.find_mid_price(lob)
        if o_type == 0:
            price, sign = do_limit_order(lob, df, scale, loc, k)
            #update_times
            times -= times[o_type]
            times[o_type] = santa_fe_4.inter_arrival(l_rate * k)


        elif o_type == 1:
            price, sign = santa_fe_4.do_market_order(lob)
            #update_times
            times -= times[o_type]
            times[o_type] = santa_fe_4.inter_arrival(m_rate * 2)


        else:
            price, sign = santa_fe_4.do_cancel_order(lob, mp)
            #update_times
            times -= times[o_type]
            times[o_type] = santa_fe_4.inter_arrival(c_rate * np.abs(lob).sum())


        lob[price] += sign
        spr[i] = santa_fe_4.find_spread(lob)
        new_mp = santa_fe_4.find_mid_price(lob)
        mid_price[i] = new_mp

    return lob, spr, mid_price

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


if __name__ == "__main__":
    rate_lim = 0.023
    rate_m   = 0.062
    rate_del = 0.103
    arr_sign = np.sign(fgn(n=300_000, hurst=0.75, length=1, method='daviesharte'))

    llob, sp, md = sim_LOB(rate_lim, rate_m, rate_del, 500, 300_000)
    plt.bar(np.arange(-250, 250), llob)
    plt.show()
    mm = md
    vol = np.sqrt(((mm[1:]- mm[:-1])**2).mean())
    print(sp.mean())
    print(vol)
    plt.hist(sp, bins = np.arange(0,50,1))
    plt.show()
    plt.plot(mm)
    plt.show()
