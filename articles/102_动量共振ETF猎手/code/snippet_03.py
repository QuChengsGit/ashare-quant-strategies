target_etf = g.ETF_list[target]
if g.signal == 'CLEAR':
    for etf in holdings:
        log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
        if etf == g.bond:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            order_value(g.bond, context.portfolio.available_cash)
    return
else:
    for etf in holdings:
        if etf == target_etf:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            log.info("------------------调仓卖出----------- %s" % (etf))
    log.info("------------------买入----------- %s" % (target))
    order_value(target_etf, context.portfolio.available_cash * g.position)
