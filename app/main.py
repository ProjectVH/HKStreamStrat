import streamlit as st
import os
import json
import logging
from datetime import date, timedelta

# helper function
def format_number(num):
    return f"{num:,}"

# Create a function to get the company name
def get_company_name(symbol):
    if symbol in stock_dict.keys():
        return stock_dict[symbol]

# client = redis.Redis(host="localhost", port=6379)

# logging.info(os.getcwd())
# get this file location
dir = os.path.dirname(__file__)

stock_market_option = "HK"

filename = os.path.join(dir, 'src', 'hk_stock_name.json')
with open(filename) as f:
    stock_dict = json.load(f)

screen = st.sidebar.selectbox(
    "View", ('', 'Strategy'), index=0)
st.title(screen)

symbol = st.sidebar.selectbox("Stock Symbol", list(stock_dict.keys()))

if screen == 'Strategy':
    from src.StreamStrat import run
    run(stock_market_option, symbol, get_company_name(symbol))

elif screen == "":
    from src.database.mongoDB import StockPriceDB
    from bokeh.plotting import figure
    from bokeh.models import ColumnDataSource, HoverTool

    dbName = 'projectValHubDB'
    colName = 'hkStockPriceData'

    failure = 1
    while failure:
        try:
            stockPriceDB = StockPriceDB(dbName, colName, os.environ["MONGO_URL"], stock_market_option)
            failure = 0
        except Exception as e:
            logging.info(e)

    collection = stockPriceDB.connectDB()
    stockPriceDB.create_index(collection)

    # download the data
    today = date.today()
    oneMonthAgo = today - timedelta(days=30)

    stockPriceDB.get_data(collection, symbol, oneMonthAgo, today)

    ## get data from db
    df = stockPriceDB.load_data(collection, symbol, oneMonthAgo, today)

    company_name = get_company_name(symbol)

    source1 = ColumnDataSource(data=df)
    # plot for close recent month
    closePlotObj = figure(x_axis_type="datetime", plot_height=350)
    closePlotObj.line(x='index', y='Close', source=source1, line_width=4)
    closePlotObj.xaxis.axis_label = 'Date'
    closePlotObj.yaxis.axis_label = f'Close Price {stock_market_option}D'

    closePlotObj.add_tools(
        HoverTool(
            tooltips=[('date', '@index{%F}'), ('close', '$@Close{0.2f}')],
            formatters={
                '@index': 'datetime'
            },
            mode="vline"
        )
    )

    # plot for volume recent month
    source2 = ColumnDataSource(data=df)
    volumePlotObj = figure(x_axis_type="datetime", plot_height=350)
    volumePlotObj.line(x='index', y='Volume', source=source2, line_width=4)
    volumePlotObj.xaxis.axis_label = 'Date'
    volumePlotObj.yaxis.axis_label = f'Volume {stock_market_option}D'

    volumePlotObj.add_tools(
        HoverTool(
            tooltips=[('date', '@index{%F}'), ('volume', '@Volume{0.00 a}')],
            formatters={
                '@index': 'datetime'
            },
            mode="vline"
        )
    )

    # Display the close prices
    st.header(company_name+" Close Price\n")
    #st.line_chart(df['Close'])
    st.bokeh_chart(closePlotObj, use_container_width=True)
    # Display the volume
    st.header(company_name+" Volume\n")
    st.bokeh_chart(volumePlotObj, use_container_width=True)
    #st.line_chart(df['Volume'])
