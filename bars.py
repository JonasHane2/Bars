import numpy as np


def numpy_ewma_vectorized(data, window):
    alpha = 2 /(window + 1.0)
    alpha_rev = 1-alpha
    n = data.shape[0]

    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]
    return out


class Bars():

    def __init__(self, bar_type="tick", avg_bar_length=100):
        self.avg_bar_length = avg_bar_length
        self.theta = 0

        self.bar_types = ["tick", "volume", "dollar"]
        self.bar_type = bar_type
        if self.bar_type not in self.bar_types:
            raise ValueError("Invalid imbalance type %s. Expected one of: %s" % (bar_type, self.bar_types))

    def get_threshold(self, trades, avg_bar_length=100):
        """
        Returns an estimate for threshold to get a bar at every N tick. 
                
        Args: 
            trade (series): information about a tick
            avg_bar_length (integer): the desired interval of every bar. 
                                      optional, set to 100. 
        Returns: 
            (number): the threshold to achieve the desired bar sampling 
                      frequency. 
        """
        avg_vol_trades = np.average(trades['Volume'])
        avg_price_trades = np.average(trades['Close'])

        if self.bar_type == "tick":
            return avg_bar_length
        elif self.bar_type == "volume":
            return avg_bar_length * avg_vol_trades
        else:
            return avg_bar_length * avg_vol_trades * avg_price_trades


    def get_inc(self, trade):
        """
        Returns the multiplication factor depending on what bar type we use.
        Tick bar returns 1
        Volume bar returns the volume of the tick
        Dollar bar returns the product of the volume and price of the tick

        Args: 
            trade (series): information about a tick
        Returns: 
            (number): factor
        """
        if self.bar_type == "volume": #Volume bar
            return trade['Volume']
        elif self.bar_type == "dollar": #Dollar bar
            return trade['Volume']*trade['Close'] 
        return 1 #Tick bar


    def get_all_bar_ids(self, trades):
        """
        Get the id of all trades that pushes the theta over the chosen
        threshold.

        Args: 
            trades (DataFrame): list of all trades
        Returns: 
            idx (list): indexes of when the threshold is reached
        """
        threshold = self.get_threshold(trades, self.avg_bar_length)

        idx =[]
        for i, row in trades.iterrows():
            self.theta += self.get_inc(row)
            if self.theta >= threshold:
                idx.append(i)
                self.theta = 0
        return idx


# TODO: extremely sensitive to initial conditions (E_T & E_imb), either 
#       very high frequency or very low and decreasing... 
#       need to find a better way to set threshold
# TODO: handle auction orders at the end of the trading day
class Imbalance_Bars(Bars):

    def __init__(self, imbalance_type="tick", E_T_init=100, E_imb_init=3000):
        super().__init__(imbalance_type, (E_T_init * abs(E_imb_init)))

        self.threshold = E_T_init * abs(E_imb_init)

        self.E_T_init = E_T_init
        self.E_T = E_T_init
        self.E_imb = E_imb_init
        
        self.b = [0] 
        self.imbalances = [] 
        self.Ts = [] 
        self.prev_price = 0 

        self.thresholds = [self.threshold]
        self.abs_thetas = [self.theta]
        self.E_Ts = [self.E_T]
        self.E_imbs = [self.E_imb]


    def tick_rule(self, curr_price):
        """
        Returns the sign of the change in closing price from time i-1 to i. 
        If there is no change, it returns the previous sign. Since b[0] is 
        initialized to 0 this value always exists. 

        Args: 
            prev_price (number): previous price
            cur_price (number): current price
        Returns: 
            (int): sign of price change (+1/-1), returns previous sign if no 
                    change
        """
        delta = curr_price - self.prev_price 
        return np.sign(delta) if delta != 0 else self.b[-1]


    def get_new_threshold(self):
        """
        Returns new threshold that the imbalance must exceed in order to 
        create a new bar.
        In theory this is the product of the excpected tick size and the 
        absolute value of the excpected imbalance. 
        Expected tick size is given as an ewma of previous tick sizes.
        Expected imbalance is given as an ewma of previous imbalances. 


        However, this can be difficult to work with. Especially when large 
        end of week auctions create very large orders that skew the values. 
        Expected imbalance is extremely sensitive to initial conditions while
        expected tick length converges to some small value for some strange 
        reason
        --- Maybe the volume should be in relation to the % of price change? 
        You can use fixed threshold and that seems to give ok results. 
        There maybe some better way of calculating the threshold. 

        Returns: 
            (number): threshold, which is the product of expected tick 
                      length and the absolute value of expected imbalance

        """
        """
        # Get expected tick size as an EWMA of previous tick sizes
        self.E_T = numpy_ewma_vectorized(np.array(self.Ts), 
                                         np.int64(len(self.Ts)))[-1]
        
        # Larger window -> pushes the threshold lower. less influenced by 
        # large bulk end of trading day orders, but generates (too) many bars 
        len_factor = 3 # chosen through experimenting with diff. values
        self.E_imb = numpy_ewma_vectorized(np.array(self.imbalances), 
                                           np.int64(self.E_T_init * len_factor))[-1] 
        #"""
        return self.E_T * abs(self.E_imb) 


    def register_new_tick(self, trade):
        """
        Registers a new tick by updating all relevant variables and checks 
        if threshold is broken. If it is then the new threshold is calculated
        and the theta is reset. 

        Args: 
            trade (series): information about a tick
        Retruns:
            (bool): True if threshold is broken, False otherwise
        """
        price = trade['Close']
        self.b.append(self.tick_rule(price)) 
        imbalance = self.b[-1] * self.get_inc(trade)
        self.imbalances.append(imbalance) 
        self.theta += imbalance 
        self.prev_price = price

        self.thresholds.append(self.threshold)
        self.abs_thetas.append(abs(self.theta))
        self.E_Ts.append(self.E_T)
        self.E_imbs.append(self.E_imb)

        if abs(self.theta) >= self.threshold:
            tick_length = len(self.imbalances) - sum(self.Ts) 
            self.Ts.append(tick_length) 
            self.threshold = self.get_new_threshold()
            self.theta = 0 
            return True 
        
        return False 


    def get_imbalance_threshold_estimates(self, trades, avg_bar_length=100):
        """
        (Bad) estimate for what the threshold should be to generate a bar 
        every n ticks
        """
        return self.get_threshold(trades, (np.log(1/avg_bar_length) / np.log(0.5)))
    

    def get_next_imbalance_id(self, trades):
        """
        Returns the id of the first imbalance bar it can find. 
        Args: 
            trades (DataFrame): list of all trades
        Returns: 
            (integer): index of when the first imbalance threshold is breached. 
                       -1 if not found. 
        """
        for i, row in trades.iterrows():
            if self.register_new_tick(row):
                return trades.index.get_loc(i)
        return -1


    def get_all_imbalance_ids(self, trades):
        """
        Returns a list of all the times when the imalance threshold
        is broken in the list of trades. 
        There is a possibility that the first tick is added twice, 
        so duplicates are removed from the list

        Args: 
            trades (DataFrame): list of all trades
        Returns: 
            (list): indexes of when the threshold is reached
        """
        #TODO fix this 
        self.E_T = 1
        self.E_imb = self.get_imbalance_threshold_estimates(trades)
        self.threshold = self.get_new_threshold()

        idx = [trades.index[0]]
        for i, row in trades.iterrows():
            if self.register_new_tick(row):
                idx.append(i)
        return list(dict.fromkeys(idx))
