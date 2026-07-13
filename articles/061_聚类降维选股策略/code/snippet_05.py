from jqdata import *
import datetime
import numpy as np
def get_stock(stockPool, begin_date):
    # 选择股票池
    if stockPool == 'AA':
        stockList = get_index_stocks('000985.XSHG', begin_date)
        stockList = [stock for stock in stockList if not stock.startswith(('3', '68', '4', '8'))]
    # 剔除ST股、停牌、新股及退市股票
    st_data = get_extras('is_st', stockList, count=1, end_date=begin_date)
    stockList = [stock for stock in stockList if not st_data[stock][0]]
    stockList = delect_stop(stockList, begin_date)
    return stockList
# 移除上市不足n天的股票
def delect_stop(stocks, beginDate, n=365):
    stockList = []
    beginDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    for stock in stocks:
        start_date = get_security_info(stock).start_date
        if start_date < (beginDate - datetime.timedelta(days=n)).date():
            stockList.append(stock)
    return stockList
# 获取股票池
current_date = datetime.datetime.now()
current_time = current_date.strftime("%Y-%m-%d")
stockList = get_stock('AA', current_time)

复制
