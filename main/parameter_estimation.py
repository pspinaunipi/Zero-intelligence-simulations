import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from numba import njit
from scipy.optimize import curve_fit





def load_LOB_data(o_name, m_name):

    header_list = ["ask price","ask vol","bid price","bid vol", "ask 2", "bid 2"]

    # import the price and volumes of the best quotes
    df_order = pd.read_csv(o_name, names = header_list, usecols = [0, 1, 2, 3, 4, 6])

    df_order["ask price"] = df_order["ask price"] / 100
    df_order["bid price"] = df_order["bid price"] / 100
    df_order["ask 2"] = df_order["ask 2"] / 100
    df_order["bid 2"] = df_order["bid 2"] / 100
    # add spread and mid price to the dataframe
    df_order["spread"] = df_order["ask price"] - df_order["bid price"]
    df_order["mid price"] = (df_order["ask price"] + df_order["bid price"]) / 2

    header_list_1 = ["time","event type","size","price","direction"]

    # import the price and volumes of the best quotes
    df_message = pd.read_csv(m_name, names = header_list_1, usecols = [0, 1, 3, 4, 5])
    df_message["price"] = df_message["price"] / 100

    df_merge = pd.concat([df_order, df_message], axis=1)

    return df_merge

def df_best_limit_prices(data,order_type):

    data = data[data["event type"] == order_type]
    data_bid = data[data["price"] == data["bid price"]]
    data_ask = data[data["price"] == data["ask price"]]
    new_data = pd.concat([data_ask,data_bid])
    new_data.sort_index(inplace=True)
    return new_data

def df_best_prices(data,order_type):
    real_indexes = []
    sec_data = data[data["event type"] == order_type]
    indexes = sec_data.index.to_numpy()

    for element in indexes:
        if element != 0:
            if sec_data["price"].at[element] == data["bid price"].at[element-1] and \
                        sec_data["direction"].at[element] == 1:
                real_indexes.append(element)
            elif sec_data["price"].at[element] == data["ask price"].at[element-1] and \
                        sec_data["direction"].at[element] == -1:
                real_indexes.append(element)

    new_data = data.loc[real_indexes]

    return new_data

def find_v0(data):
    return int(data["size"].sum()/len(data))

def find_u(data,n1,n2,n3,v):
    return data["size"].sum() / (2*v) / (n1+n2+n3)

def find_nu(data,n1,n2,n3,v):
    return data["size"].sum()/ (2*v) / (n1+n2+n3)

def find_mean_vol(data):
    v_a = data["ask vol"].mean()
    v_b = data["bid vol"].mean()
    return (v_a + v_b) / 2

def find_l(n1,n2,n3):
    return  n1 / (n1 + n2 + n3)

def find_gap_to_spread(df):
    gap_bid = (df["bid price"] - df["bid 2"]).mean()
    gap_ask = (df["ask price"] - df["ask 2"]).mean()
    gap = (np.abs(gap_bid) + np.abs(gap_ask)) / 2

    return gap / df["spread"].mean()

def del_time(data):
    new_data = data[data["time"] > 37800 ]
    final_data = new_data[new_data["time"] < 57600 - 1800]
    final_data.reset_index(inplace=True)
    return final_data

def unite_market_orders(data):
    m_data = data[data["event type"] == 4]
    m_data["time"] = (m_data["time"]*100) // 1
    grouped_market = m_data.groupby("time")["size"].sum()
    market_volume = grouped_market.sum()
    num_market = len(grouped_market)
    return num_market, market_volume


def find_quotes(data):
    quotes = data[["bid price", "bid vol", "ask price", "ask vol"]].diff().fillna(0)
    quotes["quote"] = np.ones(data.shape[0])

    # BidPrice_0 > 0
    con = (quotes["bid price"] != 0)
    a = quotes.loc[con].index.to_numpy()
    quotes.loc[a,["quote"]] = 0

    # AskPrice_0 > 0
    con = (quotes["ask price"] != 0)
    a = quotes.loc[con].index.to_numpy()
    quotes.loc[a,["quote"]] = 0

    # BidPrice_0 > 0
    con = (quotes["bid price"] == 0) & (quotes["bid vol"] != 0)
    a = quotes.loc[con].index.to_numpy()
    quotes.loc[a,["quote"]] = 0

    # AskPrice_0 > 0
    con = (quotes["ask price"] == 0) & (quotes["ask vol"] != 0)
    a = quotes.loc[con].index.to_numpy()
    quotes.loc[a,["quote"]] = 0

    return quotes["quote"].to_list()

if __name__=="__main__":


    #create a list of all the files in the folder
    dir_o ="C:\\Users\\spina\\Documents\\SOLDI\\data\\tesla_2015\\order\\"
    order_files = os.listdir(dir_o)

    dir_m ="C:\\Users\\spina\\Documents\\SOLDI\\data\\tesla_2015\\message\\"
    message_files = os.listdir(dir_m)

    lenght = len(message_files)

    mid_price = np.zeros(lenght)
    spread = np.zeros(lenght)
    lamb = np.zeros(lenght)
    nu = np.zeros(lenght)
    mu = np.zeros(lenght)
    date = np.zeros(lenght)
    shares = np.zeros(lenght)
    mean_volume = np.zeros(lenght)
    volatility = np.zeros(lenght)
    gap = np.zeros(lenght)
    i = 0

    lst_df = []

    for order, message in zip(order_files, message_files):

        filepath_order   = dir_o + order
        filepath_message = dir_m + message

        #save date
        date[i] = int(order[13:15])

        dfu = load_LOB_data(filepath_order, filepath_message)
        df = del_time(dfu)

        df["quote"] = find_quotes(df)

        #limit order at the best price
        X_lo = df.loc[(df["event type"] == 1) & (df["quote"] == 0)]
        #cancellations at the best prices
        X_c  = df.loc[(df["event type"].isin([2,3]))  & (df["quote"] == 0)]
        #market orders at the best prices (ignore hidden orders)
        N_mo, vol_mo  = unite_market_orders(df)
        N_lo  = len(X_lo)
        N_c   = len(X_c)
        tot   = N_mo + N_lo + N_c
        print(f"N_lo {N_lo}, N_mo {N_mo}, N_c {N_c}")
        #tt = df.time.max() - df.time.min()
        v0 = X_lo["size"].mean()

        mean_vol = find_mean_vol(df)
        print(mean_vol)
        mean_volume[i] = mean_vol

        u  = 0.5 / tot * vol_mo / v0
        v  = 0.5 / tot * X_c["size"].sum() / mean_vol
        l_all  = 0.5 * N_lo / tot
        n = 2 * (1 + ((X_lo["spread"] // 2).mean()))
        l = l_all / n

        mid_price[i] = df["mid price"].mean()
        spread[i] = df["spread"].mean()
        lamb[i] = l
        nu[i] = v
        mu[i] = u
        shares[i] = v0
        mp = df["mid price"].to_numpy()
        volatility[i] = np.sqrt(((mp[1:]- mp[:-1])**2).mean())
        gap[i] = find_gap_to_spread(df)
        lst_df.append(df)
        i += 1

    parameters = np.column_stack((date, mid_price, spread, lamb, nu, mu, shares, mean_volume,
                    volatility, gap))
    np.savetxt("../data/santa_fe_parameter_estimation_9.txt", parameters, delimiter = ",")
