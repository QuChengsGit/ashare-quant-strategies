def buy_stock(context, stockcode, cash):
    today_date = context.current_dt.date()
    current_data = get_current_data()
    last_price = current_data[stockcode].last_price
    if stockcode[0:3] == '688':
        if order_target_value(stockcode, cash, MarketOrderStyle(1.1 * last_price)) is not None:
            log.info('%s买入%s' % (today_date, stockcode))
    else:
        if order_target_value(stockcode, cash) is not None:
            log.info('%s买入%s' % (today_date, stockcode))
def sell_stock(context, stockcode, cash):
    today_date = context.current_dt.date()
    current_data = get_current_data()
    last_price = current_data[stockcode].last_price
    if stockcode[0:3
] == '688':
        if order_target_value(stockcode, cash, MarketOrderStyle(0.9 * last_price)) is not None:
            log.info('%s卖出%s' % (today_date, stockcode))
    else:
        if order_target_value(stockcode, cash) is not None:
            log.info('%s卖出%s' % (today_date, stockcode))
