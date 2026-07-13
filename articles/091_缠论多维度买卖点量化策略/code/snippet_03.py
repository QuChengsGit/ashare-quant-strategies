def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    security = g.security
    df = get_bars(security, count=1, unit='1m', fields=['date','open','high','low','close'])
    if df is not None:
        for row in df:
            bar = BarData(datetime=row[0], high_price=row[2], low_price=row[3], close_price=row[4])
            chan.on_bar(bar)
