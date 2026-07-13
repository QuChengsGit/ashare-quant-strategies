def industry(stockList, industry_codes, date):
    """
    计算各行业的股票数量
    """
    i_Constituent_Stocks = {}
    for code in industry_codes:
        temp = get_industry_stocks(code, date)  # 获取行业成分股
        i_Constituent_Stocks[code] = list(set(temp).intersection(set(stockList)))  # 计算股票列表和行业成分股的交集
    # 返回各行业的股票数量
    count_dict = {name: len(content_list) for name, content_list in i_Constituent_Stocks.items()}
    return count_dict

复制
