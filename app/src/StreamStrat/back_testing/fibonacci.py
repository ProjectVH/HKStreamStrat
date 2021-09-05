import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource,HoverTool,Span
from .trader import backtrader_runner

# Create a function to be used in our strategy to get the upeer fibonacci level and the lower fibonacci level of the current price
def getlevels(price,levels):
    if price >= levels[1]:
        return (levels[0], levels[1])
    elif price >= levels[2]:
        return(levels[1], levels[2])
    elif price >= levels[3]:
        return(levels[2], levels[3])
    elif price >= levels[4]:
        return(levels[3], levels[4])
    else:
        return(levels[4], levels[5])

class FibonacciRetracementLevels:

    def __init__(self,df,symbol,stake,cash):
        self.data = df.copy(deep=True)
        self.symbol = symbol
        self.stake = stake
        self.cash = cash
        # Calcualte the Fibonacci Retractment levels
        max_price = self.data['Close'].max()
        min_price = self.data['Close'].min()

        difference = max_price - min_price
        first_level = max_price - difference * 0.236
        second_level = max_price - difference * 0.382
        third_level = max_price - difference * 0.5
        fourth_level = max_price - difference * 0.618

        self.levels = [max_price,first_level,second_level,third_level,fourth_level,min_price]

    def run(self):

        # Calculate the MACD line and the Signal Line indicator

        # Calculate the Short Term exponention Moving Average
        ShortEMA = self.data.Close.ewm(span=12, adjust=False).mean()

        # Calcualte the Long term Exponentila Moving Average
        LongEMA = self.data.Close.ewm(span=26, adjust=False).mean()

        # Cacualte the Moving Average Convergence/Divergence (MACD)
        MACD = ShortEMA - LongEMA

        # Calcualte the Signal Line
        signal = MACD.ewm(span=9, adjust=False).mean()

        # Create new columns for the data frame
        self.data['MACD'] = MACD
        self.data['Signal Line'] = signal

        # to signal when to buy and when to sell the asset/stock
        buy_list = []
        sell_list = []
        flag = 0
        last_buy_price = 0

        # Loop through the data set
        for i in range(0, self.data.shape[0]):
            price = self.data['Close'][i]
            # If this is the first data point within the data set, then get the elvel above and below it
            if i == 0:
                upper_lvl, lower_lvl = getlevels(price,self.levels)
                buy_list.append(np.nan)
                sell_list.append(np.nan)
            # Else if the current price is gretaer than or equal to the upper level ot less than ot equal to the lower level, then we knoe the price has 'hit' or crossed a fibonacci level
            elif price >= upper_lvl or price <= lower_lvl:

                # Check to see if the MACD line crossed above or below the signal line
                if self.data['Signal Line'][i] > self.data['MACD'][i] and flag == 0:
                    last_buy_price = price
                    buy_list.append(price)
                    sell_list.append(np.nan)
                    # set the flag to 1 to singal that the share was bought
                    flag = 1

                elif self.data['Signal Line'][i] < self.data['MACD'][i] and flag == 1 :
                    buy_list.append(np.nan)
                    sell_list.append(price)
                    # Set the Flag to 0 to signal that the share was sold
                    flag = 0
                else:
                    buy_list.append(np.nan)
                    sell_list.append(np.nan)
            else:
                buy_list.append(np.nan)
                sell_list.append(np.nan)

            # Update the new levels
            upper_lvl, lower_lvl = getlevels(price,self.levels)

        # Create buy and sell columns
        self.data['Buy'] = buy_list
        self.data['Sell'] = sell_list


    def plotBuySell(self,stock_market_option):
        source = ColumnDataSource(data=self.data)

        p = figure(x_axis_type="datetime", plot_height=350)

        p.line(x='index', y='Close', line_alpha=0.35, source=source, legend_label="Close Price", line_color='#1f77b4',
               line_width=4)

        colors = ['red','orange','yellow','green','blue','purple']
        for level,color in zip(self.levels,colors):
            hline = Span(location=level,line_alpha=0.35,
                         dimension='width', line_color=color,
                         line_dash='dashed', line_width=4)

            p.add_layout(hline)


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
        tradeResultPlot,tradeStats = backtrader_runner(self.data,'Fibonacci',self.stake,self.cash)
        return tradeResultPlot,tradeStats



