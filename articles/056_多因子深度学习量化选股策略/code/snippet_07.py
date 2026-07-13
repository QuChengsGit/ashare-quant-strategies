def filter_all_stock2(context, stock_list):
    by_date = get_trade_days(end_date=context.previous_date, count=180)[0]
    all_stocks = get_all_securities(date=by_date).index.tolist()
    stock_list = list(set(stock_list).intersection(set(all_stocks)))
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (
            stock.startswith(('3', '68', '4', '8')) or  # 创业板、科创板、北交所
            curr_data[stock].paused or curr_data[stock].is_st or
            ('ST' in curr_data[stock].name) or ('*' in curr_data[stock].name) or
            ('退' in curr_data[stock].name) or
            curr_data[stock].day_open == curr_data[stock].high_limit or
            curr_data[stock].day_open == curr_data[stock].low_limit
    )]
def order_target_value_(security, value):
    log.debug("Order %s to value %f" % (get_security_info(security).display_name, value))
    return order_target_value(security, value)
def open_position(security, value):
    order = order_target_value_(security, value)
    return order is not None and order.filled > 0
def close_position(position):
    order = order_target_value_(position.security, 0)
    return order is not None and order.status == OrderStatus.held and order.filled == order.amount

复制
