def filter_highprice_stock(context, stock_list):
    prices = history(1, '1m', 'close', stock_list).iloc[0]
    threshold = prices.quantile(0.75)
    result = prices[prices < threshold].index.tolist()
    return result
