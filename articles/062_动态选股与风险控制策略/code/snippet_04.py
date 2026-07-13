def do_buy(context):
    hold_num = len(context.portfolio.positions)
    if hold_num >= g.max_hold_num:
        log.info("满仓中")
        return
    holdable_num = g.max_hold_num - hold_num
    cash = context.portfolio.available_cash / holdable_num
    chosen_stocks = g.chosen_stocks
    current_data = get_current_data()
    for stock in chosen_stocks:
        if stock in context.portfolio.positions:
            log.info("不买已经持有的股票%s" % stock)
            continue
        if stock in g.need_sell:
            log.info("不买满足卖出条件没有卖出的股票%s" % stock)
            continue
        if ((context.portfolio.positions[stock].closeable_amount != 0) and (current_data[stock].last_price < current_data[stock].high_limit)):
            log.info("已经涨停无法买入%s" % stock)
            continue
        if open_position(stock, cash):
            if len(context.portfolio.positions) >= g.max_hold_num:
                break
