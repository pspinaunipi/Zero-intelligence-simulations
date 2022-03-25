#@title Importa moduli e funzioni utili
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from numba import njit
from scipy.optimize import curve_fit
import scipy.stats
from santa_fe_2 import *

if __name__ == "__main__":
    df = pd.read_csv("PP.csv")
    for element in pd.unique(df["DF type"]):
        sns.scatterplot(data = df[df["DF type"] == element], y = "MeanSpread", x = "SimSpread", label=element)
        x = np.arange(50,250,10)
        plt.plot(x,x)
        plt.legend()
        plt.show()

    x = np.linspace(0,0.002,10)
    for element in pd.unique(df["DF type"]):
        sns.scatterplot(data = df[df["DF type"] == element], y = "Volatility", x = "SimVolatility", label=element)
        plt.plot(x,x)
        plt.legend()
        plt.show()
