import os
import numpy as np
import yfinance as yf
import plotly.express as px
from bars import Imbalance_Bars, Bars


def pearson_autocorrelation_test(data, print_txt=False):
    """
    Pearson correlation coefficient.
    Testing significantly non-zero autocorrelation. 
    
    Args: 
        data (list): list of values to be tested
    Returns: 
        (bool): true if test is passed, false otherwise
    """
    res = np.corrcoef(data[:-1], data[1:])
    p = res[0][1]
    return p
    
    alpha = 0.05
    if print_txt:
        print("Pearson correlation coefficient: {}".format(res))

    return abs(p)>alpha


if __name__ == '__main__':
    directory = os.path.dirname(os.path.realpath(__file__)) + '/plots/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    symbol = "CL=F" #WTI crude futures
    instr = yf.Ticker(symbol) 

    bar_types = ["tick", "volume", "dollar"]
    E_T_init = [1, 10, 100]
    E_imb_init = [5, 300, 3000]
    time_periods = ["1d", "7d", "30d"]
    interval = ["1m", "1m", "30m"]

    labels = dict(x="Time interval", y="Bar-type", color="Pearson-corr.")
    x = ["Period {}, Interval {}.".format(x, y) for x, y in zip(time_periods, interval)] # time intervals
    y = ["Time", "TB", "TIB", "VB", "VIB", "DB", "DIB"] # bar types
    res = []

    for tp, i in zip(time_periods, interval):

        temp = []
        
        # Time bars
        hist = instr.history(period=tp, interval=i)
        hist_delta = [hist['Close'][x] - hist['Close'][x-1] for x in range(1, len(hist['Close']))]
        temp.append(round(pearson_autocorrelation_test(hist_delta), 3))

        for bt, et, ei in zip(bar_types, E_T_init, E_imb_init):

            # Bars
            b = Bars(bar_type=bt, avg_bar_length=20)
            b_idx = b.get_all_bar_ids(hist)
            b_hist = [hist['Close'][x] for x in b_idx]
            b_hist_delta = [b_hist[x] - b_hist[x-1] for x in range(1, len(b_hist))]
            temp.append(round(pearson_autocorrelation_test(b_hist_delta), 3))


            # Imbalance bars
            ib = Imbalance_Bars(imbalance_type=bt, E_T_init=et, E_imb_init=(ei))
            ib_idx = ib.get_all_imbalance_ids(hist)
            ib_hist = [hist['Close'][x] for x in ib_idx]
            ib_hist_delta = [ib_hist[x] - ib_hist[x-1] for x in range(1, len(ib_hist))]
            temp.append(round(pearson_autocorrelation_test(ib_hist_delta), 3))
        
        res.append(temp)

    fig = px.imshow(np.array(res).T, labels=labels, x=x, y=y, text_auto=True, color_continuous_scale='RdBu_r') 
    fig.write_image(directory+'pearson_corr.png')