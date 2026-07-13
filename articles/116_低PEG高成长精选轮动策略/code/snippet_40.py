all_positions = context.portfolio.positions
current_data = get_current_data()
for stock in all_positions:
    if (stock not in g.buy_list) and (stock not in g.high_limit_list):
        limit_price = current_data[stock].last_price * 0.9
        order_target(stock, 0, MarketOrderStyle(limit_price))
        log.info("日常调仓卖出 [%s]" % stock)
    else:
        log.info("日常调仓，继续持有 [%s]" % stock)

复制
