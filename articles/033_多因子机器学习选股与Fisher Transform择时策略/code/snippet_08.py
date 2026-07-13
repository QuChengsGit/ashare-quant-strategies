def order_stock_sell(context, order_list):
    for stock in context.portfolio.positions:
        if stock not in order_list:
            order_target_value(stock, 0)
def order_stock_buy(context, order_list):
    if len(context.portfolio.positions) < g.stocknum:
        num = g.stocknum - len(context.portfolio.positions)
        g.each_stock_cash = context.portfolio.cash / num
    for stock in order_list:
        if stock not in context.portfolio.positions:
            order_target_value(stock, g.each_stock_cash)
