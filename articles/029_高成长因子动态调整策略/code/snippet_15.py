def basic_filters(context, stock_list):
    yesterday = context.previous_date
    current_data = get_current_data()
    return [stock for stock in stock_list if not (
        current_data[stock].is_st or
        'ST' in current_data[stock].name or
        '*' in current_data[stock].name or
        '退' in current_data[stock].name or
        yesterday - get_security_info(stock).start_date <= datetime.timedelta(days=375) or
        current_data[stock].paused
    )]
def clear_account(context):
    if g.is_empty_position:
        for stock in context.portfolio.positions:
            limit
_price = get_current_data()[stock].last_price * 0.9
            order_target(stock, 0, MarketOrderStyle(limit_price))

复制
