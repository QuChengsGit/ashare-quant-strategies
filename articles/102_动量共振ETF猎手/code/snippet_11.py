if (context.current_dt.hour == 11 and g.niu_signal == 0 and g.signal == 'BUY') or (context.current_dt.hour == 14 and g.niu_signal == 1):
    log.info('牛熊不匹配，这个时间点不能开仓，并清仓')
    for etf in holdings:
        if etf == g.bond:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            order_value(g.bond, context.portfolio.available_cash)
    return
if today_increase > g.dapan_threshold and today_increase > 0.05 * today_increase_previous and target_bbi < 1:
    g.signal = 'BUY'
    g.increase_days += 1
else:
    g.signal = 'CLEAR'
    g.decrease_days += 1
log.info("-------------increase_days----------- %s" % (g.increase_days))
log.info("-------------decrease_days----------- %s" % (g.decrease_days))
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
