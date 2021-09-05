import numpy as np
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource,HoverTool
from .trader import backtrader_runner

class SimpleMovingAverage:
    def __init__(self,df,symbol,stake,cash):
        self.data = df.copy(deep=True)
        self.symbol = symbol
        self.stake = stake
        self.cash = cash

    def run(self):
        # Create the simple moving average with a 30 day window (30 MA)
        SMA30 = pd.DataFrame()
        SMA30['Adj Close Price'] = self.data['Adj Close'].rolling(window=30).mean()

        # Create the simple moving 100 day average (100 MA)

        SMA100 = pd.DataFrame()
        SMA100['Adj Close Price'] = self.data['Adj Close'].rolling(window=100).mean()

        # Create a new data frame ot store all the data
        self.data['SMA30'] = SMA30['Adj Close Price']
        self.data['SMA100'] = SMA100['Adj Close Price']

        # To signal when to buy and when to sell the asset/stock
        sigPriceBuy = []
        sigPriceSell = []
        flag = -1

        for i in range(len(self.data)):
            if self.data['SMA30'][i] > self.data['SMA100'][i]:
                if flag != 1:
                    sigPriceBuy.append(self.data['Adj Close'][i])
                    sigPriceSell.append(np.nan)
                    flag = 1
                else:
                    sigPriceBuy.append(np.nan)
                    sigPriceSell.append(np.nan)
            elif self.data['SMA30'][i] < self.data['SMA100'][i]:
                if flag != 0:
                    sigPriceBuy.append(np.nan)
                    sigPriceSell.append(self.data['Adj Close'][i])
                    flag = 0
                else:
                    sigPriceBuy.append(np.nan)
                    sigPriceSell.append(np.nan)
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)

        # Store the buy and sell data into a variable
        self.data['Buy'] = sigPriceBuy
        self.data['Sell'] = sigPriceSell

    def plotBuySell(self,stock_market_option):

        source = ColumnDataSource(data=self.data)

        p = figure(x_axis_type="datetime", plot_height=350)

        p.line(x='index', y='Adj Close', line_alpha=0.35, source=source, legend_label="Close Price",
               line_color='#1f77b4', line_width=4)

        p.line(x='index', y='SMA30', line_alpha=0.35, source=source, legend_label='SMA30', line_color='#d62728',
               line_width=4)

        p.line(x='index', y='SMA100', line_alpha=0.35, source=source, legend_label='SMA100', line_color='#ff7f0e',
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
        tradeResultPlot,tradeStats = backtrader_runner(self.data,'SMA',self.stake,self.cash)
        return tradeResultPlot,tradeStats



