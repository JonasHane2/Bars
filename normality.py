import os
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from scipy.stats import shapiro, normaltest, anderson
from statsmodels.graphics.gofplots import qqplot
from bars import Imbalance_Bars, Bars


def shapiro_wilk_test(data, print_txt=False):
    """
    Shapiro-Wilk test for normality 
    (null hypothesis: proposes that no statistical significance exists in a 
    set of given observations and is used to assess the credibility of a 
    hypothesis by using sample data)
    (p-value: statistical measure used to determine the likelihood that an 
    observed outcome is the result of chance. if p<=0.05 the null hypothesis
    is rejected)

    Args: 
        data (list): list of values to be tested
    Returns: 
        (bool): true if test is passed, false otherwise
    """
    stat, p = shapiro(data)
    """
    if print_txt:
        print('Statistics=%.3f, p=%.3f' % (stat, p)) ####
    return p>0.05
    #"""
    return p


def dagostino_k2_test(data, print_txt=False):
    """
    D'Agostino's K^2 test for normality 

    Args: 
        data (list): list of values to be tested
    Returns: 
        (bool): true if test is passed, false otherwise
    """
    stat, p = normaltest(data)
    """
    if print_txt:
        print('Statistics=%.3f, p=%.3f' % (stat, p)) ####
    return p>0.05
    #"""
    return p


def anderson_darling_test(data, print_txt=False):
    """
    Anderson-Darling test for normality 

    Args: 
        data (list): list of values to be tested
    Returns: 
        (bool): true if test is passed, false otherwise
    """
    stat = anderson(data)
    if print_txt:
        print('Statistic: %.3f' % stat.statistic) ####
    normal = True

    for i in range(len(stat.critical_values)):
        sl = stat.significance_level[i]
        cv = stat.critical_values[i]
        if stat.statistic < cv:
            if print_txt: 
                print('%.3f: %.3f, data looks normal (fail to reject H0)' % (sl, cv))
        else: 
            if print_txt:
                print('%.3f: %.3f, data does not look normal (reject H0)' % (sl, cv))
            normal = False
    
    return normal


def create_dist_histogram(data, labels, bin_size):
    """
    Creates a histogram of the distribution and compares it to the Normal dist.
    """
    
    histogram_ti = ff.create_distplot([np.array(data)], labels, curve_type='kde', bin_size=bin_size)
    temp_hist_ti = ff.create_distplot([np.array(data)], labels, curve_type='normal', bin_size=bin_size)
    normal_x = temp_hist_ti.data[1]['x']
    normal_y = temp_hist_ti.data[1]['y']
    histogram_ti.add_traces(go.Scatter(x=normal_x, y=normal_y, mode = 'lines',
                                    line = dict(color='rgba(0,255,0, 0.6)',
                                        #dash = 'dash'
                                        width = 1),
                                    name = 'normal'))
    histogram_ti.update_layout(title=('Num datapoints: %s. Distribution of returns: mean=%.3f stdv=%.3f' % (len(data), np.mean(data), np.std(data))))

    return histogram_ti
    histogram_ti.show()


def create_qq_plot(data, title):
    """
    Create Quantile-Quantile plot for checking distribution- 
    """
    #Supress annoying warning. not good idea
    import warnings 
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        qqplot_data = qqplot(data, line='s').gca().lines
        fig = go.Figure()

    fig.add_trace({
        'type': 'scatter',
        'x': qqplot_data[0].get_xdata(),
        'y': qqplot_data[0].get_ydata(),
        'mode': 'markers',
        'marker': {
            'color': '#19d3f3'
        }
    })

    fig.add_trace({
        'type': 'scatter',
        'x': qqplot_data[1].get_xdata(),
        'y': qqplot_data[1].get_ydata(),
        'mode': 'lines',
        'line': {
            'color': '#636efa'
        }
    })


    fig['layout'].update({
        'title': 'Quantile-Quantile Plot'+title,
        'xaxis': {
            'title': 'Theoritical Quantities',
            'zeroline': False
        },
        'yaxis': {
            'title': 'Sample Quantities'
        },
        'showlegend': False,
        'width': 800,
        'height': 700,
    })
    return fig
    fig.show()


def concatenate_figures(figs):

    pass


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
    imbalance_types = bar_types
    E_T_init = [1, 10, 100]
    E_imb_init = [5, 300, 3000]
    time_periods = ["1d", "7d", "30d"]
    interval = ["1m", "1m", "30m"]

    #CLT needs >30 samples

    x = ["Period {}, Interval {}.".format(x, y) for x, y in zip(time_periods, interval)] # time intervals
    y = ["Time", "TB", "TIB", "VB", "VIB", "DB", "DIB"] # bar types
    shapiro_wilk_res = []
    dagostino_k2_res = []

    #"""
    for tp, i in zip(time_periods, interval):

        sw_res = []
        dk2_res = []
        figs_qq = []
        figs_dist = []

        hist = instr.history(period=tp, interval=i)
        hist_delta = [hist['Close'][x] - hist['Close'][x-1] for x in range(1, len(hist['Close']))]
        sw_res.append(round(shapiro_wilk_test(hist_delta[:5000]), 3))
        dk2_res.append(round(dagostino_k2_test(hist_delta[:5000]), 3))

        figs_qq.append(create_qq_plot(np.array(hist_delta), (' time, time period: '+tp+', interval: '+i)))
        figs_dist.append(create_dist_histogram(hist_delta, [('Distplot time-bar, time period: '+tp+', interval: '+i)], 0.05))
        
        for bt, et, ei in zip(bar_types, E_T_init, E_imb_init):
            
            b = Bars(bar_type=bt, avg_bar_length=20)
            b_idx = b.get_all_bar_ids(hist)
            b_hist = [hist['Close'][x] for x in b_idx]
            b_hist_delta = [b_hist[x] - b_hist[x-1] for x in range(1, len(b_hist))]
            sw_res.append(round(shapiro_wilk_test(b_hist_delta), 3))
            dk2_res.append(round(dagostino_k2_test(b_hist_delta), 3))

            figs_qq.append(create_qq_plot(np.array(b_hist_delta), (' '+bt+'-Bar, time period: '+tp+', interval: '+i)))
            figs_dist.append(create_dist_histogram(b_hist_delta, [('Distplot '+bt+'-Bar, time period: '+tp+', interval: '+i)], 0.5))
        
            ib = Imbalance_Bars(imbalance_type=bt, E_T_init=et, E_imb_init=(ei)) #*int(tp[:-1])*int(i[:-1])
            ib_idx = ib.get_all_imbalance_ids(hist)
            ib_hist = [hist['Close'][x] for x in ib_idx]
            ib_hist_delta = [ib_hist[x] - ib_hist[x-1] for x in range(1, len(ib_hist))]
            sw_res.append(round(shapiro_wilk_test(ib_hist_delta), 3))
            dk2_res.append(round(dagostino_k2_test(ib_hist_delta), 3))

            figs_qq.append(create_qq_plot(np.array(ib_hist_delta), (' '+bt+'-IB, time period: '+tp+', interval: '+i)))
            figs_dist.append(create_dist_histogram(ib_hist_delta, [('Distplot '+bt+'-IB, time period: '+tp+', interval: '+i)], 0.5))
            
            #print("Time period {} and interval {}. Num datapoints: {}. Avg IB length: {}.".format(tp, i, len(ib_hist_delta), (len(hist)/len(ib_idx))))
            #print('Distribution of returns: mean=%.3f stdv=%.3f' % (np.mean(ib_hist_delta), np.std(ib_hist_delta)))
            #print("Tests: Shapiro-Wilk: {}, D'Agostino's K^2: {}, Anderson-Darling: {}.".format(shapiro_wilk_test(ib_hist_delta), dagostino_k2_test(ib_hist_delta), anderson_darling_test(ib_hist_delta)))            

        shapiro_wilk_res.append(sw_res)
        dagostino_k2_res.append(dk2_res)
        """
        fig_dist = make_subplots(rows=1, cols=3, specs=[[{"type": "distplot"}, {"type": "distplot"}, {"type": "distplot"}]])
        fig_dist.add_trace(figs_dist[0][0], row=1, col=1)
        fig_dist.add_trace(figs_dist[1][0], row=1, col=2)
        fig_dist.add_trace(figs_dist[2][0], row=1, col=3)
        fig_dist.show()
        #"""
        #prøve å lage 3x7 plots for både qq og dist

        figures_to_html(figs_qq, directory+'qq_plots_'+tp+'_'+i+'.html')
        figures_to_html(figs_dist, directory+'dist_histograms_'+tp+'_'+i+'.html')

    
    fig_sw = px.imshow(np.array(shapiro_wilk_res).T, labels=dict(x="Time interval", y="Bar-type", color="Shapiro-Wilk\np-value"), x=x, y=y, text_auto=True, color_continuous_scale='RdBu_r') 
    fig_sw.write_image(directory+'sw_test.png')
    fig_dk2 = px.imshow(np.array(dagostino_k2_res).T, labels=dict(x="Time interval", y="Bar-type", color="D'Agostino's K^2\np-value"), x=x, y=y, text_auto=True, color_continuous_scale='RdBu_r') 
    fig_dk2.write_image(directory+'dk2_test.png')