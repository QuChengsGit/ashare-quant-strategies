def trade_stocks(context):
    cdata = get_current_data()
    # 卖出不在待买入列表中的股票
    for s in context.portfolio.positions:
        if s not in g.buylist:
            log.info('Sell', s, cdata[s].name)
            order_target(s, 0)
    # 买入待买入股票
    position_count = len(context.portfolio.positions)
    if g.stock_num > position_count:
        psize = context.portfolio.available_cash / (g.stock_num - position_count)
        for s in g.buylist:
            if s not in context.portfolio.positions:
                log.info('buy', s, cdata[s].name)
                order_value(s, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break

复制
