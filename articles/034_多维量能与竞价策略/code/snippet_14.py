def call_auction(context):
    log.info('函数运行时间(Call_auction)：' + str(context.current_dt.time()))
    current_data = get_current_data()
    today_date = context.current_dt.date()
    lastd_date = context.previous_date
    buy_list = []
    df_auction = get_call_auction(g.poollist, start_date=today_date, end_date=today_date, fields=['time', 'current', 'volume', 'money'])
    if len(g.sell_list) == 0:
        log.info('今日早盘无卖信')
    else:
        for stockcode in context.portfolio.positions:
            if not current_data[stockcode].paused and stockcode in g.sell_list:
                sell_stock(context, stockcode, 0)
    for i in range(len(df_auction)):
        stockcode = df_auction.code.values[i]
        price = df_auction.current.values[i]
        df_price = get_price(stockcode, end_date=lastd_date, frequency='daily', fields=['close'], count=5)
        if g.auction_open_lowlimit < price / df_price.close[-1] < g.auction_open_highlimit:
            buy_list.append(stockcode)
    if len(buy_list) == 0:
        log.info('今日无买信')
        return
    log.info('今日买信共%d只:' % len(buy_list))
    total_value = context.portfolio.total_value
    buy_cash = 0.5 * total_value / len(buy_list)
    for stockcode in buy_list:
        if stockcode not in context.portfolio.positions:
            buy_stock(context, stockcode, buy_cash)

复制
