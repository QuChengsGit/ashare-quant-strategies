def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st]
def get_recent_limit_up_stock(context, stock_list, recent_days):
    stat_date = context.previous_date
    return get_price(stock_list, end_date=stat_date, frequency='daily', fields=['close', 'high_limit'],
                     count=recent_days, panel=False, fill_paused=False).query('close==high_limit').code.tolist()
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[
stock][-1] < current_data[stock].high_limit]
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or last_prices[stock][-1] > current_data[stock].low_limit]
def close_position(position):
    order = order_target_value(position, 0)
    if order is not None and order.status == OrderStatus.held and order.filled == order.amount:
        return True
    return False
