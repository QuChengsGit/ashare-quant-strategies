def function_buy(context, stock):
    open_cash = 0
    stock_owner = context.portfolio.positions
    if len(stock_owner) < 20:
        open_cash = context.portfolio.available_cash / (20 - len(stock_owner))
    if stock not in stock_owner and open_cash > 5000:
        order_value(stock, open_cash)
