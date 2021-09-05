import backtrader as bt

class PandasDEMA(bt.feeds.PandasData):
    lines = ('dema_short','dema_long','buy_signal','sell_signal')
    params = (
        ('datetime', None),
        ('open',None),
        ('high',None),
        ('low',None),
        ('close',"Close"),
        ('volume',None),
        ('openinterest',None),
        ('adj_close',None),
        ('dema_short', 'DEMA_short'),
        ('dema_long', 'DEMA_long'),
        ('buy_signal', 'Buy'),
        ('sell_signal','Sell')
    )


class PandasOBV(bt.feeds.PandasData):
    lines = ('obv','obv_ema','buy_signal','sell_signal')
    params = (
        ('datetime', None),
        ('open',None),
        ('high',None),
        ('low',None),
        ('close',"Close"),
        ('volume',None),
        ('openinterest',None),
        ('adj_close',None),
        ('obv', "OBV"),
        ('obv_ema', "OBV_EMA"),
        ('buy_signal', 'Buy'),
        ('sell_signal','Sell')
    )

class PandasSMA(bt.feeds.PandasData):
    lines = ('sma30','sma100','buy_signal','sell_signal')
    params = (
        ('datetime', None),
        ('open',None),
        ('high',None),
        ('low',None),
        ('close',"Close"),
        ('volume',None),
        ('openinterest',None),
        ('adj_close',None),
        ('sma30', "SMA30"),
        ('sma100', "SMA100"),
        ('buy_signal', 'Buy'),
        ('sell_signal','Sell')
    )

class PandasFibonacci(bt.feeds.PandasData):
    lines = ('macd','signal_line','buy_signal','sell_signal')
    params = (
        ('datetime', None),
        ('open',None),
        ('high',None),
        ('low',None),
        ('close',"Close"),
        ('volume',None),
        ('openinterest',None),
        ('adj_close',None),
        ('macd', "MACD"),
        ('signal_line', "Signal Line"),
        ('buy_signal', 'Buy'),
        ('sell_signal','Sell')
    )