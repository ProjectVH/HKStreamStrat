import backtrader as bt
import math
#import datetime
#from strategies.strategy import TestStrategy
from .pandasDataLoader import PandasDEMA,PandasOBV,PandasSMA,PandasFibonacci
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

"""
def processPlots(cerebro, numfigs=1, iplot=True, start=None, end=None,
         width=16, height=9, dpi=300, use=None, **kwargs):

    # if self._exactbars > 0:
    #     return
    from backtrader import plot
    import matplotlib
    matplotlib.use('agg')

    if cerebro.p.oldsync:
        plotter = plot.Plot_OldSync(**kwargs)
    else:
        plotter = plot.Plot(**kwargs)

    plotter = plot.Plot(**kwargs)

    figs = []
    for stratlist in cerebro.runstrats:
        for si, strat in enumerate(stratlist):
            rfig = plotter.plot(strat, figid=si * 100,
                                numfigs=numfigs, iplot=iplot,
                                start=start, end=end, use=use,)
            figs.append(rfig)

        # this blocks code execution
        # plotter.show()

    for fig in figs:
        for f in fig:
            f.set_size_inches(width, height)
            f.set_dpi(dpi)
            f.savefig('broker_fig.png', bbox_inches='tight')
    return figs
"""

class TestStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.sell_signal = self.datas[0].sell_signal
        self.buy_signal = self.datas[0].buy_signal

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            #raise ValueError("maybe you don't have enough cash")
            # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            if not(math.isnan(self.buy_signal[0])):
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(exectype=bt.Order.Close)
        else:
            if not(math.isnan(self.sell_signal[0])):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(exectype=bt.Order.Close)


class TradeStat(bt.analyzers.TradeAnalyzer):
    '''
    statistics for trade:
    col:
    for all trade:
        index1:
            total - total # of trade
            closed - total # of closed trade
        index2:
            total - total profit/loss of all trade
            return - return rate for investment

    col:
    for won trade:
        index1:
            closed - total # of closed trade
            percent - % of won close trade from all closed trade
        index2:
            total  - total profit from won trade
            max - max profit from won trade

    for lost trade:
        index1:
            closed - total # of closed trade
            percent - % of lost close trade from all closed trade
        index2:
            total  - total profit from lost trade
            max - max profit from lost trade
    '''


    def __init__(self):
        self.start_val = self.strategy.broker.getvalue()
        self.end_val = None
    def stop(self):
        self.end_val = self.strategy.broker.getvalue()
    def get_analysis(self):
        dict1 = super(TradeStat, self).get_analysis()
        ## handling case for no trade happen(no closed trade/no enough cash)
        if len(dict1.keys())==1:
            return 0
        result1 = []
        result2 = []
        total_close = 0
        for key,val in dict1.items():
            if key == 'total':
                temp1 = {'col':'ALL TRADES','id1':'TRADE','id2':'total','val':str(val['total'])}
                temp2 = {'col':'ALL TRADES','id1':'TRADE','id2':'closed','val':str(val['closed'])}
                total_close = val['closed']

            elif key == 'pnl':
                total_profit = val['gross']['total']
                ret_rate = total_profit / self.start_val
                temp1 = {'col': 'ALL TRADES', 'id1':'PROFIT','id2': 'total', 'val': "{:.4f}".format(total_profit)}
                temp2 = {'col': 'ALL TRADES', 'id1':'PROFIT','id2': 'return rate', 'val': "{:.4%}".format(ret_rate)}

            elif key == 'won':
                temp1 = {'col': 'TRADES WON', 'id1':'TRADE','id2': 'total', 'val': str(val['total'])}
                temp2 = {'col': 'TRADES WON', 'id1':'TRADE','id2': '%', 'val': "{:.4f}".format(val['total']/total_close )}
                temp3 = {'col': 'TRADES WON', 'id1':'PROFIT','id2': 'total', 'val': "{:.4f}".format(val['pnl']['total'])}
                temp4 = {'col': 'TRADES WON', 'id1':'PROFIT','id2': 'max', 'val': "{:.4f}".format(val['pnl']['max'])}

            elif key == 'lost':
                temp1 = {'col': 'TRADES LOST', 'id1':'TRADE','id2': 'total', 'val': str(val['total'])}
                temp2 = {'col': 'TRADES LOST', 'id1':'TRADE','id2': '%', 'val': "{:.4f}".format(val['total']/total_close )}
                temp3 = {'col': 'TRADES LOST', 'id1':'PROFIT','id2': 'total', 'val': "{:.4f}".format(val['pnl']['total'])}
                temp4 = {'col': 'TRADES LOST', 'id1':'PROFIT','id2': 'max', 'val': "{:.4f}".format(val['pnl']['max'])}
            else:
                continue

            if key in ['total','pnl']:
                for _dict in [temp1,temp2]:
                    result1.append(_dict)
            if key in ['won','lost']:
                for _dict in [temp1,temp2,temp3,temp4]:
                    result2.append(_dict)

        return {'result1':result1,'result2':result2}


def backtrader_runner(df,strategy_name,stake,cash):
    cerebro = bt.Cerebro()
    ## too much stake?
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)

    cerebro.broker.set_cash(cash)
    # Analyzer
    cerebro.addanalyzer(TradeStat, _name='trade_stat')
    #data = backtrader.feeds.YahooFinanceCSVData(
    #    dataname='data/GOOG.csv',plot=False)
        # Do not pass values before this date
        #fromdate=datetime.datetime(2001, 10, 1),
        # Do not pass values after this date
        #todate=datetime.datetime(2001, 12, 1),
        #reverse=False)
    if strategy_name == 'SMA':
        data = PandasSMA(dataname = df,plot = False)
        cerebro.addstrategy(TestStrategy)
    elif strategy_name == 'OBV':
        data = PandasOBV(dataname = df,plot = False)
        cerebro.addstrategy(TestStrategy)
    elif strategy_name == 'DEMA':
        data = PandasDEMA(dataname = df,plot = False)
        cerebro.addstrategy(TestStrategy)
    elif strategy_name == 'Fibonacci':
        data = PandasFibonacci(dataname = df,plot = False)
        cerebro.addstrategy(TestStrategy)

    cerebro.adddata(data)

    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    thestrats = cerebro.run()
    ## for getting the analyzer obj
    thestrat = thestrats[0]

    #print('Final Portfolio Value: %.2  f' % cerebro.broker.getvalue())
    #processPlots(cerebro,width=12, height=6, dpi=300,fmt_x_ticks = '%x',)

    b = Bokeh(plot_mode='single', output_mode='memory',scheme=Tradimo(show_headline = False,plotaspectratio = 2.0))
    model = cerebro.plot(b)
    return model[0],thestrat.analyzers.trade_stat.get_analysis()


