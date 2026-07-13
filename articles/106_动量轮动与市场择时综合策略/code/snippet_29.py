def adjust_position(context, buy_stock, stock_position):
    value = context.portfolio.cash / (g.stock_tobuy - len(context.portfolio.positions))
    open_position(buy_stock, value)

复制
