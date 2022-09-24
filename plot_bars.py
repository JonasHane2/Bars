import os
from bars import Imbalance_Bars, Bars
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def figures_to_html(figs, filename="dashboard.html"):
    """
    Write figures to html file
    """
    with open(filename, 'w') as dashboard:
        dashboard.write("<html><head></head><body>" + "\n")
        for fig in figs: 
            inner_html = fig.to_html().split('<body>')[1].split('</body>')[0]
            dashboard.write(inner_html)
        dashboard.write("</body></html>" + "\n")


if __name__ == '__main__':
    directory = os.path.dirname(os.path.realpath(__file__)) + '/plots/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    symbol = "CL=F" #WTI crude futures
    instr = yf.Ticker(symbol)

    bar_types = ["tick", "volume", "dollar"]
    time_periods = ["1d", "7d", "30d"]
    interval = ["1m", "1m", "30m"]
    E_T_init = [1, 10, 100]
    E_imb_init = [5, 300, 3000]

    for tp, i in zip(time_periods, interval):

        b_figs = []
        ib_figs = []

        hist = instr.history(period=tp, interval=i)
        hist_delta = [hist['Close'][x] - hist['Close'][x-1] for x in range(1, len(hist['Close']))]

        print("\nTime period: {}, Interval: {}.".format(tp, i))


        for bt, et, ei in zip(bar_types, E_T_init, E_imb_init):

            b = Bars(bar_type=bt, avg_bar_length=20)
            b_idx = b.get_all_bar_ids(hist)
            b_hist = [hist['Close'][x] for x in b_idx]
            b_hist_delta = [b_hist[x] - b_hist[x-1] for x in range(1, len(b_hist))]

            print("{}-Bar. Num ticks: {}. Mean tick length: {}".format(bt, len(b_idx), (len(hist)/len(b_idx))))
           
            # Plot with closing price, imbalance points and volume
            b_fig1 = make_subplots(specs=[[{"secondary_y": True}]])
            b_fig1.update_layout(title_text=bt+"-Bar with time period: "+tp+", and interval: "+i+".")
            b_fig1.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price'), secondary_y=False)
            b_fig1.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'), secondary_y=True)
            b_fig1.add_trace(go.Scatter(x=hist.loc[b_idx].index, y=hist.loc[b_idx]['Close'], mode='markers', name='DIB', marker_symbol='x', marker_color='black', marker_size=12), secondary_y=False)

            b_figs.append(b_fig1)



            ib = Imbalance_Bars(imbalance_type=bt, E_T_init=et, E_imb_init=(ei)) #*int(tp[:-1])*int(i[:-1])
            ib_idx = ib.get_all_imbalance_ids(hist)
            ib_hist = [hist['Close'][x] for x in ib_idx]
            ib_hist_delta = [ib_hist[x] - ib_hist[x-1] for x in range(1, len(ib_hist))]
            
            print("{}-IB. Num ticks: {}. Mean tick length: {}".format(bt, len(ib_idx), (len(hist)/len(ib_idx))))

            ib_fig = make_subplots(specs=[[{"secondary_y": True}]])
            ib_fig.update_layout(title_text=bt+"-IB with time period: "+tp+", and interval: "+i+".")
            ib_fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price'), secondary_y=False)
            ib_fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'), secondary_y=True)
            ib_fig.add_trace(go.Scatter(x=hist.loc[ib_idx].index, y=hist.loc[ib_idx]['Close'], mode='markers', name='DIB', marker_symbol='x', marker_color='black', marker_size=12), secondary_y=False)


            ib_fig_sp = make_subplots(rows=2, cols=2)
            ib_fig_sp.update_layout(title_text=bt+"-IB with time period: "+tp+", and interval: "+i+".")

            ib_fig_sp.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price'), row=1, col=1)
            #ib_fig_sp.add_trace(go.Ohlc(x=hist.loc[ib_idx].index, open=hist.loc[ib_idx]['Open'], high=hist.loc[ib_idx]['High'], low=hist.loc[ib_idx]['Low'], close=hist.loc[ib_idx]['Close']))
            #ib_fig_sp.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'), row=1, col=1) #kanskje droppe
            ib_fig_sp.add_trace(go.Scatter(x=hist.loc[ib_idx].index, y=hist.loc[ib_idx]['Close'], mode='markers', name='IB', marker_symbol='x', marker_color='black', marker_size=12), row=1, col=1)
            
            ib_fig_sp.add_trace(go.Scatter(x=[x for x in range(len(ib.abs_thetas))], y=ib.abs_thetas, name='abs_Thetas'), row=1, col=2)
            ib_fig_sp.add_trace(go.Scatter(x=[x for x in range(len(ib.thresholds))], y=ib.thresholds, name='Threshold'), row=1, col=2)
            
            ib_fig_sp.add_trace(go.Ohlc(x=hist.loc[ib_idx].index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'], name="Price"), row=2, col=1)
            #ib_fig_sp.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'), row=2, col=1)
            #ib_fig_sp.add_trace(go.Scatter(x=hist.loc[ib_idx].index, y=hist.loc[ib_idx]['Close'], mode='markers', name='IB', marker_symbol='x', marker_color='black', marker_size=12), row=2, col=1)

            ib_fig_sp.add_trace(go.Scatter(x=[x for x in range(len(ib.imbalances))], y=ib.imbalances, name='imbs'), row=2, col=2)
            ib_fig_sp.add_trace(go.Scatter(x=[x for x in range(len(ib.E_imbs))], y=ib.E_imbs, name='E_imbs'), row=2, col=2) #makes no sense now

            ib_figs.append(ib_fig)
            ib_figs.append(ib_fig_sp)
        
        figures_to_html(b_figs, directory+"bars_"+tp+"_"+i+".html")
        figures_to_html(ib_figs, directory+"imbalance_bars_"+tp+"_"+i+".html")

