def filter_stock_ST(stock_list):
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (curr_data[stock].paused or curr_data[stock].is_st or 'ST' in curr_data[stock].name or '*' in curr_data[stock].name or '退' in curr_data[stock].name)]
def filter_stock_limit(stock_list):  
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (curr_data[stock].high_limit <= curr_data[stock].day_open or curr_data[stock].day_open <= curr_data[stock].low_limit)]
def remove_new_stocks(security_list, context):
    return [stock for stock in security_list if (context.current_dt.date() - get_security_info(stock).start_date).days >= 180]
