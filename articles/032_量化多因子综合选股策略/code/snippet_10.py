def my_adjust_position(context, hold_stocks):
    free_value = context.portfolio.total_value
    maxpercent = 1.3 / g.buy_stock_count
    buycash = free_value / g.buy_stock_count
    for stock in context.portfolio.positions.keys():
        current_data = get_current_data()
        price1d = get_close_price(stock, 1)
        nosell_1 = context.portfolio.positions[stock].price >= current_data[stock].high_limit
        sell_2 = stock not in hold_stocks
        if sell_2 and not nosell_1:
            close_position(stock)
        else:
            current_percent = context.portfolio.positions[stock].value / context.portfolio.total_value
            if current_percent > maxpercent:
                order_target_value(stock, buycash)

复制
