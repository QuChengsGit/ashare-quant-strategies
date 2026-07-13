def do_sell(context):
    if len(context.portfolio.positions) < 1:
        log.info("空仓没什么可卖的")
        return
    pos = context.portfolio.positions
    for stock in pos:
        if pos[stock].closeable_amount <= 0:
            continue
        if is_limitup(stock):
            log.info("%s 涨停的不卖" % stock)
            continue
        if stock in g.chosen_stocks:
            log.info("%s 还在选股范围内的不卖" % stock)
            continue
        if check_earn(pos[stock], 12) and scream_sell(stock, context.current_dt + dt.timedelta(minutes=-10), pos[stock].price):
            log.info("卖出{}, scream_sell".format(stock))
            g.need_sell.add(stock)
        if check_hold_days(pos[stock]):
            log.info("卖出{}, check_hold_days".format(stock))
            g.need_sell.add(stock)
        if big_volume_sell(stock, pos[stock].price, context):
            log.info("卖出{}, big_volume_sell".format(stock))
            g.need_sell.add(stock)
        if check_earn(pos[stock], 15):
            log.info("卖出{}, check_earn".format(stock))
            g.need_sell.add(stock)
    for stock in g.need_sell.copy():
        if close_position(pos[stock]):
            g.need_sell.remove(stock)
