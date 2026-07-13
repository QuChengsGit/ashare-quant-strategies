def market_run(context):
    log.info('函数运行时间(market_close):' + str(context.current_dt.time()))
    current_data = get_current_data()
    for stockcode in context.portfolio.positions:
        if not current_data[stockcode].paused and current_data[stockcode].last_price != current_data[stockcode].high_limit:
            log.info('非涨停即出%s' % stockcode)
            sell_stock(context, stockcode, 0)

复制
