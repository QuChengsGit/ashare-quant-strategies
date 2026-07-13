def filter_paused_stock(stock_list):
    return [stock for stock in stock_list if not get_current_data()[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st and 'ST' not in current_data[stock].name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
def filter_kcbj_stock(stock_list):
    return [stock for stock in stock_list if stock[0] not in ['4', '8'] and not stock.startswith('68')]
def filter_limitup_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions or current_data[stock].close < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions or current_data[stock].close > current_data[stock].low_limit]
def filter_new_stock(context, stock_list):
    return [stock for stock in stock_list if context.previous_date - get_security_info(stock).start_date >= datetime.timedelta(days=375)]

复制
