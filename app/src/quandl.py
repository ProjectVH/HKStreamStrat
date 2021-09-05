import requests
import pandas as pd

class QuandlStock:
    def __init__(self, token, symbol):
        self.BASE_URL = "https://www.quandl.com/api/v3/datasets/HKEX"
        self.token = token
        self.symbol = symbol

    def get_stock_price(self,start = None ,end = None):
        url = f"{self.BASE_URL}/{self.symbol}?order=asc&start_date={start}&end_date={end}&api_key={self.token}"
        r = requests.get(url)
        return r.json()["dataset"]["data"]

    @staticmethod
    def get_symbols():
        """
        url = f"https://www.quandl.com/api/v3/databases/HKEX/metadata?api_key={self.token}"
        r = requests.get(url)
        import zipfile, io
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall()
        """

        """
        stock_list = pd.read_csv("HKEX_metadata.csv", usecols=["code","name","description"])
        condit1 = stock_list["description"].str.contains("Stock Prices")
        condit2 = stock_list["description"].str.contains("Currency: HKD")
        stock_list = stock_list[np.logical_and(condit1,condit2)]
        result = dict()
        for code, company_name in zip(stock_list["code"],stock_list["name"]):
            result[code] = company_name

        import json
        with open('hk_stock_name.json', 'w') as fp:
            json.dump(result, fp)
        """
        def addZeroForCode(Code):
            """
            Ensure code being five digit
            """
            codeLength = len(Code)
            newCode = (5-codeLength)*"0" + Code
            return newCode

        url = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
        stock_list = pd.read_excel(url, header=2, converters= {"Stock Code":addZeroForCode},
                                   usecols=["Stock Code","Name of Securities","Category","Board Lot"])
        stock_list = stock_list[stock_list["Category"] == "Equity"]
        result = dict()
        result1 = dict()
        for code, company_name, lotSize in zip(stock_list["Stock Code"],stock_list["Name of Securities"],
                                      stock_list["Board Lot"]):
            lotSize = "".join(lotSize.split(","))
            result[code] = company_name
            result1[code] = int(lotSize)

        import json
        with open('hk_stock_name.json', 'w') as fp:
            json.dump(result, fp)
        with open('hk_stock_lot_size.json', 'w') as fp:
            json.dump(result1, fp)