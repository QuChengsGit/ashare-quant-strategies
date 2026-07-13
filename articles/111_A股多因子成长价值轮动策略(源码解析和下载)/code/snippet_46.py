position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        value = context.portfolio.cash / (g.stock_num - position_count)
        for stock in buy_stocks:
            if stock not in context.portfolio.positions:
                open_position(stock, value)
                if len(context.portfolio.positions) >= g.stock_num: break

复制
