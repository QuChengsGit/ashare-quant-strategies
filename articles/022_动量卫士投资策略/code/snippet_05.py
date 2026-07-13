def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68')]
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list
            if not current_data[stock].is_st
            and 'ST' not in current_data[stock].name
            and '*' not in current_data[stock
].name]
def filter_limitup_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price > current_data[stock].low_limit]
def filter_highprice_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if current_data[stock].last_price <= 50]
def now_vol(context, stock):
    return history(1, '1d', 'volume', [stock]).iloc[0].values[0]
def ma_vol(context, stock, days):
    return history(days, '1d', 'volume', [stock]).mean()
