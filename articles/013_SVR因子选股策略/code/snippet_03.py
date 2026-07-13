def handle_trader(context):
    # 获取交易参数
    choice = g.choice
    psize = g.psize
    cdata = get_current_data()
    # 卖出不在选股中的股票
    for s in context.portfolio.positions:
        if s not in choice and not cdata[s].paused:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, LimitOrderStyle(cdata[s].last_price))
    # 买入选中的股票
    for s in choice:
        if context.portfolio.available_cash < psize:
            break
        if s not in context.portfolio.positions and not cdata[s].paused:
            log.info('buy', s, cdata[s].name)
            order_value(s, psize, LimitOrderStyle(cdata[s].last_price))
