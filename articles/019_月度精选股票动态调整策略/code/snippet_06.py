def prepare_stock_list(context):
    g.hold_list = []
    g.high_limit_list = []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if g.hold_list:
        for stock in g.hold_list:
            df = get_price(stock, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=1)
            if df['close'][0] >= df['high_limit'][0] * 0.98:
                g.high_limit_list.append(stock)
