def mybuy(context):
    hold_stocks = g.chosen_stock_list
    if len(hold_stocks) < g.buy_stock_count:
        g.buy_stock_count = len(hold_stocks)
        log.info("Adjusted buy_stock_count to {} as there are fewer stocks in hold_stocks.".format(g.buy_stock_count))
    free_value = context.portfolio.total_value
    minpercent = 0.7 / g.buy_stock_count
    buycash = free_value / g.buy_stock_count
    free_cash = free_value - context.portfolio.positions_value
    min_buy = context.portfolio.total_value / (g.buy_stock_count * 10)
    for i in range(g.buy_stock_count):
        if len(context.portfolio.positions) >= g.buy_stock_count:
            break
        stock = hold_stocks[i]
        if free_cash <= min_buy:
            break
        position = context.portfolio.positions.get(stock)
        current_percent = position.value / context.portfolio.total_value if position else 0
        if current_percent >= minpercent:
            continue
        tobuy = min(free_cash, buycash - position.value) if position else min(buycash, free_cash)
        order_value(stock, tobuy)
        free_cash -= tobuy

复制
