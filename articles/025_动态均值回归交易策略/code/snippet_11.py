def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + context.current_dt.strftime("%Y-%m-%d %H:%M:%S"))
    g.not_buy_flg = 1
    g.not_sell_flg = 1
    g.last_buy_orderid = None
    g.last_sell_orderid = None
    g.last_buy_price = 0
    g.last_sell_price = 0
    g.price_50m = {'open': 0.000, 'close': 0.000, 'high': 0.000, 'low': 0.000}
    g.price_before_close = 0.000

复制
