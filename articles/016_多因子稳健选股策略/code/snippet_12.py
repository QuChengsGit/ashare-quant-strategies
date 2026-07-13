def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions:
        current_data = get_current_data()
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        sell_2 = stock not in buy_stocks
        if sell_2 and not nosell_1:
            log.info("调出平仓：[%s]" % (stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("已持仓，本次不买入：[%s]" % (stock))
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.cash / (g.buy_stock_count - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break

复制
