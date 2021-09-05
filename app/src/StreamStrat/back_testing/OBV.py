import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource,HoverTool
from .trader import backtrader_runner


class OnBalanceVolume:
    def __init__(self,df,symbol,stake,cash):
        self.data = df.copy(deep=True)
        self.symbol = symbol
        self.stake = stake
        self.cash = cash

    def run(self):
        # Calcualte the on Blaance Volume (OBV)
        OBV = []
        OBV.append(0)

        # Loop throught the data set (close proce) from the second row (index 1) to the end of the data set
        for i in range(1, len(self.data.Close)):
            if self.data.Close[i] > self.data.Close[i - 1]:
                OBV.append(OBV[-1] + self.data.Volume[i])
            elif self.data.Close[i] < self.data.Close[i - 1]:
                OBV.append(OBV[-1] - self.data.Volume[i])
            else:
                OBV.append(OBV[-1])

        # Store the OBV and OBV Exponential Moving Average (EMA) into new column
        self.data['OBV'] = OBV
        self.data['OBV_EMA'] = self.data['OBV'].ewm(span=20).mean()

        # to signal when to buy and when to sell the asset/stock
        sigPriceBuy = []
        sigPriceSell = []
        flag = -1

        # Loop through the length of the data set
        for i in range(0, len(self.data)):
            # If OBV > OBV_EMA Then Buy--> col1 =>'OBV' and col2 => 'OBV_EMA'
            if self.data['OBV'][i] > self.data['OBV_EMA'][i] and flag != 1:
                sigPriceBuy.append(self.data['Close'][i])
                sigPriceSell.append(np.nan)
                flag = 1
            # If OBV < OBV_EMA Then Sell
            elif self.data['OBV'][i] < self.data['OBV_EMA'][i] and flag != 0:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(self.data['Close'][i])
                flag = 0
            else:
                sigPriceSell.append(np.nan)
                sigPriceBuy.append(np.nan)

        self.data['Buy'] = sigPriceBuy
        self.data['Sell'] = sigPriceSell

    def plotBuySell(self,stock_market_option):

        source = ColumnDataSource(data=self.data)

        p = figure(x_axis_type="datetime", plot_height=350)

        p.line(x='index', y='Close', line_alpha=0.35, source=source, legend_label="Close Price", line_color='#1f77b4',
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
        tradeResultPlot,tradeStats = backtrader_runner(self.data,'OBV',self.stake,self.cash)
        return tradeResultPlot,tradeStats

