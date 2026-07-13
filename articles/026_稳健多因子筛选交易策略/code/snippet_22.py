def filter_highprice_stock(context, stock_list):
    df = history(1, unit='1m', field='close', security_list=stock_list)
    price_list = df.values[0].copy()
    price_list.sort()
    price = price_list[int(0.75 * len(df.T))]
    return [stock for stock in stock_list if df[stock][-1] < price]

复制
