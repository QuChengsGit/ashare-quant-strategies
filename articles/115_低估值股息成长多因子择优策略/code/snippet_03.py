def trade_stocks(context):
    current_data = get_current_data()
    # 卖出不在买入名单中的股票
    for stock in context.portfolio.positions:
        if stock not in g.buylist:
            order_target_value(stock, 0)
            log.info("卖出 {}".format(stock))
    # 计算剩余资金并买入新股票
    cash = context.portfolio.cash
    target_value = cash / (g.stock_num - len(context.portfolio.positions))
    for stock in g.buylist:
        if stock not in context.portfolio.positions:
            order_value(stock, target_value)
            log.info("买入 {}".format(stock))
