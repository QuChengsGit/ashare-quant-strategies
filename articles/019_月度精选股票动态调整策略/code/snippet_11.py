def filter_limit_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() or (current_data[stock].low_limit < last_prices[stock][-1] < current_data[stock].high_limit)]
