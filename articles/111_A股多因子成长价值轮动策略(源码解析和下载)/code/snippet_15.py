def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [s for s in stock_list if not current_data[s].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [s for s in stock_list if not current_data[s].is_st and 'ST' not in current_data[s].name and '*' not in current_data[s].name and '退' not in current_data[s].name]
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [s for s in stock_list if s in context.portfolio.positions or last_prices[s][-1] < current_data[s].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [s for s in stock_list if s in context.portfolio.positions or last_prices[s][-1] > current_data[s].low_limit]
def filter_kcb_stock(context, stock_list): return [s for s in stock_list if not s.startswith('688')]
def filter_new_stock(context, stock_list):
    yesterday = context.previous_date
    return [s for s in stock_list if (yesterday - get_security_info(s).start_date).days >= 250]
def today_is_between(context, start_date, end_date):
    today = context.current_dt.strftime('%m-%d')
    return start_date <= today <= end_date
