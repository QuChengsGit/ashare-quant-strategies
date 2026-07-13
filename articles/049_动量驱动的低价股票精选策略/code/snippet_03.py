def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # 卖出不再持有的股票
    for stock in g.security1:
        order_target(stock, 0)
    # 买入新选中的股票
    cash = context.portfolio.available_cash / len(g.security2)
    for stock in g.security2:
        order_value(stock, cash)
