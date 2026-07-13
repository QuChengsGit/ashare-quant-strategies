def sell_stock_security(date: str, total_value: float, stocks: list):
    for stock in stocks:
        order_target(stock, 0)
    if g.mode == 1:
        g.mode = 0
    elif g.mode == 2:
        g.mode = 0
    elif g.mode == 0:
        g.mode = 2

复制
