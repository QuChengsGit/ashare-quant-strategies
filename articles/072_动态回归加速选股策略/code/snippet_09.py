def check_limit_up(context):
    now_time = context.current_dt
    for stock in g.yesterday_HL_list:
        current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
        if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
            log.info("[%s]涨停打开，卖出" % (stock))
            order_value(stock, 0)
        else:
            log.info("[%s]
涨停，继续持有" % (stock))
    if g.etf:
        order_value(g.etf, context.portfolio.available_cash)
