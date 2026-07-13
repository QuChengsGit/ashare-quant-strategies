def iTrader(context):
    choice = g.choice 
    position_size = g.position_size 
    lm_value = 0.8 * position_size 
    hm_value = 1.2 * position_size 
    cdata = get_current_data() 
    # 卖出不在选股池中的股票
    for s in context.portfolio.positions:
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue
        if s not in choice:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, MarketOrderStyle(0.99*cdata[s].last_price))
    # 买入或调整仓位
    for s in choice:
        if context.portfolio.available_cash < position_size:
            break
        if cdata[s].paused or cdata[s].last_price >= cdata[s].high_limit or cdata[s].last_price <= cdata[s].low_limit:
            continue
        if s not in context.portfolio.positions:
            log.info('buy', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01*cdata[s].last_price))
        elif context.portfolio.positions[s].value < lm_value:
            log.info('balance+', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(1.01*cdata[s].last_price))
        elif context.portfolio.positions[s].value > hm_value:
            log.info('balance-', s, cdata[s].name)
            order_target_value(s, position_size, MarketOrderStyle(0.99*cdata[s].last_price))
