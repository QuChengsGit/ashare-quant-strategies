def before_market_open(context):
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    all_data = get_current_data()
    # 止损控制
    if g.lostcontrol != 0:
        holdlist = list(context.portfolio.positions)
        g.selllist = lost_control(context, holdlist, today_date)
        log.info('%s损控-%s卖出:' % (today_date, g.lostcontrol))
        log.info(g.selllist)
    # 判断是否是换仓日
    if (g.day_count % g.shiftdays == 0):
        log.info('今天是换仓日，开仓')
        g.adjustpositions = True
    else:
        log.info('今天是旁观日，持仓')
        g.adjustpositions = False
        return
    # 生成股票池
    stocklist = generate_stock_pool(context, today_date, lastd_date)
    g.buylist = select_stocks(context, stocklist)
    log.info('今日买信:')
    log.info(g.buylist)
