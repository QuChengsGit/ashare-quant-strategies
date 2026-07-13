def get_recent_limit_up_stock(context, stock_list, recent_days):
    new_list = []
    for stock in stock_list:
        df = get_price(stock, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit'], count=recent_days, panel=False)
        if df[df['close'] == df['high_limit']].empty:
            new_list.append(stock)
    return new_list
def check_limit_up(context):
    for stock in g.high_limit_list:
        current_data = get_price(stock, end_date=context.current_dt, frequency='1m', fields=['close', 'high_limit'], count=1, panel=False)
        if current_data.iloc[0, 0] < current_data.iloc[0, 1] * 1.1:
            limit_price = current_data.iloc[0, 0] * 0.8
            order_target(stock, 0, MarketOrderStyle(limit_price))
            log.info("[%s]涨停打开，卖出" % (stock))

复制
