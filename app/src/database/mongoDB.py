
import pymongo
import os
import pandas as pd

from ..iex import IEXstock
from ..quandl import QuandlStock
from datetime import timezone, timedelta, date, datetime
from pymongo import ASCENDING


class MongoDB:
    def __init__(self, dbName, colName, MONGO_URL):
        self.dbName = dbName
        self.colName = colName
        self.MONGO_URL = MONGO_URL

    def connectDB(self):
        """
        make connection to database and collection
        :return: collection
        """
        dbName = self.dbName
        colName = self.colName
        dbConn = pymongo.MongoClient(self.MONGO_URL)
        db = dbConn[dbName]
        collection = db[colName]
        return collection

class StockPriceDB(MongoDB):
    def __init__(self, dbName, colName, MONGO_URL, stockMarketOption ):
        super(StockPriceDB, self).__init__(dbName, colName, MONGO_URL)
        self.stockMarketOption = stockMarketOption

    # helper function
    def __datetime2str(self, time):
        return time.strftime('%Y-%m-%d')

    def __process_iex_data(self, dict1):
        df = pd.DataFrame(dict1)
        df = df[['date', 'uclose', 'uhigh', 'ulow', 'uopen', 'fclose', 'uvolume', 'symbol']]
        df['date'] = pd.to_datetime(df['date'], unit='ms').apply(self.__datetime2str)
        df.set_axis(['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'symbol'], axis='columns',
                    inplace=True)
        df['date_obj'] = pd.to_datetime(df['Date'])
        return df

    def __process_quandl_data(self, symbol, list2d):
        ## supress warning
        pd.options.mode.chained_assignment = None

        data = pd.DataFrame(list2d)
        df = data[[0, 7, 8, 1, 9, 10]]
        df.set_axis(['Date', 'High', 'Low', 'Close', 'Previous Close', 'Volume'], axis='columns', inplace=True)
        df["Volume"] = df["Volume"] * 1000
        df['Date'] = pd.to_datetime(df['Date'])
        df['date_obj'] = pd.to_datetime(df['Date'])
        df["symbol"] = symbol
        return df

    def get_data(self, collection, symbol, start, end):

        """
        check whether there is updated stock data in database
        if not, get stock price data, process it and store it into database
        """

        if collection.count_documents({'symbol': symbol}) > 0:
            last = collection.find({'symbol': symbol}, {"_id": 0}).sort(
                "date_obj", -1).limit(1)
            startNew = list(last)[0]['Date']
            delta1 = timedelta(days=3)
            if (pd.to_datetime(end) - pd.to_datetime(startNew)) > delta1 and self.stockMarketOption == "US":
                stock = IEXstock(os.environ["IEX_TOKEN"], symbol)
                dict1 = stock.getOHLC(startNew, str(end))
                df = self.__process_iex_data(dict1)
                collection.insert_many(df.to_dict('records'))

            elif (pd.to_datetime(end) - pd.to_datetime(startNew)) > delta1 and self.stockMarketOption == "HK":
                stock = QuandlStock(os.environ["QUANDL_TOKEN"], symbol)
                list2d = stock.get_stock_price(startNew, str(end))
                df = self.__process_quandl_data(symbol, list2d)
                collection.insert_many(df.to_dict('records'))

        else:
            if self.stockMarketOption == "US":
                stock = IEXstock(os.environ["IEX_TOKEN"], symbol)
                ## get recent 2yrs data
                dict1 = stock.getOHLC(range=True)
                df = self.__process_iex_data(dict1)
                collection.insert_many(df.to_dict('records'))
            else:
                stock = QuandlStock(os.environ["QUANDL_TOKEN"], symbol)
                today = date.today()
                threeYrsAgo = today - timedelta(days=3 * 365)
                list2d = stock.get_stock_price(str(threeYrsAgo), str(today))
                df = self.__process_quandl_data(symbol, list2d)
                collection.insert_many(df.to_dict('records'))

    def load_data(self, collection, symbol, start, end):
        """
        load data from database given user query and return data frame for model
        :return:data frame
        """

        table = collection.find(
            {'symbol': symbol, "date_obj": {"$gte": pd.to_datetime(start), "$lt": pd.to_datetime(end)}
             }, {"_id": 0, 'symbol': 0})
        df = pd.DataFrame(list(table))
        df.set_index("date_obj", drop=True, inplace=True)
        df.index.name = 'index'

        return df

    def create_index(self, collection):
        """
        given collection, create index for query and sorting
        """
        collection.create_index([("symbol", ASCENDING), ("date_obj", ASCENDING)], name="compoundIndex")

class StockFundaDB(MongoDB):

    def __init__(self, dbName, colName, MONGO_URL ):
        super(StockFundaDB, self).__init__(dbName, colName, MONGO_URL)

    # helper function
    def __create_cache(self, data, cache_key):
        cached_obj = dict()
        cached_obj['data'] = data
        cached_obj['cache_key'] = cache_key
        cached_obj['expireAt'] = datetime.now(timezone.utc) + timedelta(hours=24)
        return cached_obj

    def save_cache(self, collection, data, cache_key):
        """
        given key and fundamental data, create cache and save it into database
        """
        cache = self.__create_cache(data, cache_key)
        collection.insert_one(cache)

    def find_cache(self, collection, cache_key):
        """
        given key, find corresponding cache and return its data
        :return: data of the dictionary cache
        """
        cache = collection.find_one({'cache_key': cache_key}, {
            "_id": 0, 'cache_key': 0, 'expireAt': 0})
        return cache

    def create_index(self, collection):

        """
        given collection, create index for query and auto expire
        """

        collection.create_index([('cache_key', 1)])
        collection.create_index([('expireAt', 1)], expireAfterSeconds=0)
