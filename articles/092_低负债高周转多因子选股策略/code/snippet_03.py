def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        if stock not in buy_stocks:
            order_target(stock, 0)  # 卖出不在新股票池中的股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash * g.position / (g.stock_num - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                order_target_value(stock, value)
                if len(context.portfolio.positions) == g.stock_num:
                    break
