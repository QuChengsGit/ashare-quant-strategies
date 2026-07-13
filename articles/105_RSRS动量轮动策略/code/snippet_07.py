def market_open(context):
    stock = list(context.portfolio.positions.keys())
    security = ''.join(stock)
    if g.timing_signal == 'SELL' and security != '511880.XSHG' and security != '':
        if security == g.check_out_list:
            order = order_target_value(security, 0)
        elif get_timing_signal(context, security) == 'SELL':
            order = order_target_value(security, 0)
    elif g.timing_signal == 'BUY' and g.check_out_list != security:
        order_target_value(security, 0)
        order_value(g.check_out_list, context.portfolio.available_cash)
    if context.portfolio.positions_value == 0:
        order_value('511880.XSHG', context.portfolio.available_cash)
