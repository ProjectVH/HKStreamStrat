import os
import streamlit as st
import pandas as pd

from datetime import timedelta,date
from ..database.mongoDB import StockPriceDB

from .back_testing.DEMA import DoubleExponentialMovingAverage
from .back_testing.OBV import OnBalanceVolume
from .back_testing.SMA import SimpleMovingAverage
from .back_testing.fibonacci import FibonacciRetracementLevels
# from config import mongo_connect_str,IEX_TOKEN

today = date.today()
threeYrsAgo = today - timedelta(days=3*365)

def getLotSize(symbol):
    dir = os.path.dirname(__file__)
    filename = os.path.join(os.path.dirname(dir), 'hk_stock_lot_size.json')
    import json
    with open(filename) as f:
        stock_lost_dict = json.load(f)
    if symbol in stock_lost_dict.keys():
        return stock_lost_dict[symbol]

# Create a function to get user input
def get_input(stock_market_option, symbol):
    start_date = st.sidebar.date_input("Start date", threeYrsAgo)
    end_date = st.sidebar.date_input("End date", today)

    if stock_market_option == "US":
        default_stake = 1
        strategy_choices = ('DEMA', 'OBV', 'SMA','Fibonacci')
    else:
        default_stake = getLotSize(symbol)
        strategy_choices = ('DEMA', 'OBV', 'Fibonacci')

    selected_strategy = st.sidebar.selectbox('Chosen strategy', strategy_choices)
    stake = st.sidebar.number_input('Stake', min_value=default_stake, max_value=None, value= default_stake)
    cash = st.sidebar.number_input('Cash',  min_value=1, max_value=None, value= 100000 )

    return start_date, end_date, selected_strategy, stake, cash


def run(stock_market_option,symbol,company_name):
    st.write(f"""
    ## Stock Market Web Application 
    **Stock price data** , date range from {threeYrsAgo.strftime('%b %d, %Y')} to {today.strftime('%b %d, %Y')}
    """)

    # ADD side bar header
    st.sidebar.header('User Input')

    # Set the index to be the date
    start, end, chosen_strategy, stake ,cash = get_input(stock_market_option, symbol)


    dbName = 'projectValHubDB'
    if stock_market_option == "US": colName = 'stockPriceData'
    else: colName = 'hkStockPriceData'

    stockPriceDB = StockPriceDB(dbName, colName, os.environ["MONGO_URL"], stock_market_option)
    collection = stockPriceDB.connectDB()
    stockPriceDB.create_index(collection)

    # download the data
    stockPriceDB.get_data(collection, symbol, start, end)
    ## get data from db
    df = stockPriceDB.load_data(collection, symbol, start, end)

    # Display the close prices
    st.header(company_name+" Close Price\n")
    st.line_chart(df['Close'])

    # Display the volume
    st.header(company_name+" Volume\n")
    st.line_chart(df['Volume'])

    if chosen_strategy == 'DEMA':
        dema = DoubleExponentialMovingAverage(df, symbol, stake, cash)
        dema.run()
        plot_obj = dema.plotBuySell(stock_market_option)
        tradeResultPlot,tradeStats = dema.plotBackTesting()
    elif chosen_strategy == 'OBV':
        obv = OnBalanceVolume(df, symbol, stake, cash)
        obv.run()
        plot_obj = obv.plotBuySell(stock_market_option)
        tradeResultPlot, tradeStats = obv.plotBackTesting()
    elif chosen_strategy == 'SMA':
        sma = SimpleMovingAverage(df, symbol, stake, cash)
        sma.run()
        plot_obj = sma.plotBuySell(stock_market_option)
        tradeResultPlot, tradeStats = sma.plotBackTesting()
    elif chosen_strategy == 'Fibonacci':
        fibonacci = FibonacciRetracementLevels(df, symbol, stake, cash)
        fibonacci.run()
        plot_obj = fibonacci.plotBuySell(stock_market_option)
        tradeResultPlot, tradeStats = fibonacci.plotBackTesting()

    # handling case of no trade happened
    if tradeStats:
        st.bokeh_chart(plot_obj, use_container_width=True)

        #broker_fig = Image.open("broker_fig.png")
        #st.image(broker_fig, use_column_width=True)
        st.bokeh_chart(tradeResultPlot, use_container_width=True)

        # create trade stats table
        st.header('Trades Statistics')
        df_stats1 = pd.DataFrame(tradeStats['result1'])
        df_stats2 = pd.DataFrame(tradeStats['result2'])

        table1 = df_stats1.pivot(
            index=['id1', 'id2'], columns='col', values='val')
        table2 = df_stats2.pivot(
            index=['id1', 'id2'], columns='col', values='val')
        table1.sort_values(by='id1', ascending=False,
                           kind='heapsort', inplace=True)
        table2.sort_values(by='id1', ascending=False,
                           kind='heapsort', inplace=True)
        col1, col2 = st.columns(2)
        with col1:
            st.table(table1)
        with col2:
            st.table(table2)
    else:
        st.bokeh_chart(plot_obj, use_container_width=True)
        st.markdown(
            "<h3 style='text-align: center;'><strong>No Closed Trade Happened.</strong></h3>", unsafe_allow_html=True)

# Get statistics on the data
#st.header('Data Statistics')
# st.write(df.describe())
