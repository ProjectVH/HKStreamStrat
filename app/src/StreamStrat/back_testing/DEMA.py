import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource,HoverTool
from .trader import backtrader_runner

# Create a function to calcualte the Double Exponential Moving Average (DEMA)
def DEMA(data, time_period, column):
    # Calcualte DEMA
    EMA = data[column].ewm(span=time_period, adjust=False).mean()
    DEMA = 2*EMA - EMA.ewm(span=time_period, adjust=False).mean()

    return DEMA

class DoubleExponentialMovingAverage:
    def __init__(self,df,symbol,stake,cash):
        self.data = df.copy(deep=True)
        self.symbol = symbol
        self.stake = stake
        self.cash = cash

    def run(self):
        self.data['DEMA_short'] = DEMA(self.data, 20, 'Close')
        self.data['DEMA_long'] = DEMA(self.data, 50, 'Close')
        # To buy and sell the stock (The trading strtegy)
        buy_list = []
        sell_list = []
        flag = False
        # Loop through the data
        for i in range(0, len(self.data)):
            if self.data['DEMA_short'][i] > self.data['DEMA_long'][i] and flag == False:
                buy_list.append(self.data['Close'][i])
                sell_list.append(np.nan)
                flag = True
            elif self.data['DEMA_short'][i] < self.data['DEMA_long'][i] and flag == True:
                buy_list.append(np.nan)
                sell_list.append(self.data['Close'][i])
                flag = False
            else:
                buy_list.append(np.nan)
                sell_list.append(np.nan)

        # store buy and sell signal/lists into the data set
        self.data['Buy'] = buy_list
        self.data['Sell'] = sell_list

    def plotBuySell(self,stock_market_option):
        source = ColumnDataSource(data=self.data)

        p = figure(x_axis_type="datetime", plot_height=350)

        p.line(x='index', y='Close', line_alpha=0.35, source=source, legend_label="Close Price", line_color='#1f77b4',
               line_width=4)

        p.line(x='index', y='DEMA_short', line_alpha=0.35, source=source, legend_label='DEMA_short',
               line_color='#d62728',
               line_width=4)

        p.line(x='index', y='DEMA_long', line_alpha=0.35, source=source, legend_label='DEMA_long', line_color='#ff7f0e',
               line_width=4)

        buy_scatter = p.scatter(x='index', y='Buy', marker="triangle",
                                source=source, legend_label='Buy Signal', color='green', size=5)

        sell_scatter = p.scatter(x='index', y='Sell', marker="inverted_triangle",
                                 source=source, legend_label='Sell Signal', color='red', size=5)

        p.legend.location = "top_left"
        p.title.text = self.symbol + ' Close Price Buy and Sell Signals'
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = f'Close Price {stock_market_option}D'

        p.add_tools(
            HoverTool(
                tooltips=[('date', '@index{%F}'), ('close', '$@Close{0.2f}')],
                formatters={
                    '@index': 'datetime'
                },
                mode="vline",
                renderers=[buy_scatter, sell_scatter])
        )
        return p

    def plotBackTesting(self):
        tradeResultPlot,tradeStats = backtrader_runner(self.data,'DEMA',self.stake,self.cash)
        return tradeResultPlot,tradeStats



