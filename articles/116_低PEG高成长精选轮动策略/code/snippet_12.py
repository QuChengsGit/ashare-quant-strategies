no_hold_target_num = g.total_stock_num - len(context.portfolio.positions)
if no_hold_target_num > 0:
    cash_per_stock = context.portfolio.available_cash / float(no_hold_target_num)
    for stock in g.buy_list:
        if stock not in g.hold_list:
            limit_price = current_data[stock].last_price * 1.1
            order_target_value(stock, cash_per_stock, MarketOrderStyle(limit_price))
            log.info("买入目标股票 [%s]，目标市值：%.2f" % (stock, cash_per_stock))
