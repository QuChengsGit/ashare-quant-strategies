def filter_limit_stock(context, stock_list):
    current_data = get_current_data()
    holdings = list(context.portfolio.positions)
    return [stock for stock in stock_list if (stock in holdings) or
            current_data[stock].low_limit < current_data[stock].last_price < current_data[stock].high_limit]
def filter_kcb_stock(stock_list):
    return [stock for stock in stock_list if not stock.startswith('68')]
