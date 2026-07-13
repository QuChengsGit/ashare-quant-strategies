def initHandleParam():
    g.buy_list = []
def get_stock_price(stock_list, ed, days):
    stock_price = get_price(security=stock_list, end_date=ed, frequency='1d', fields=['close', 'volume'],
                            panel=False, count=days, skip_paused=True)
    return stock_price
def getday3(d, step):
    day = d + datetime.timedelta(step)
    return day
def buy_stock(context, stock):
    need_count = g.buy_stock_limit - len(context.portfolio.positions.keys())
    if need_count == 0:
        return
    buy_cash = context.portfolio.available_cash / need_count
    order_value(stock, buy_cash)
def sell_stock(stock, value):
    order_target(stock, value)
