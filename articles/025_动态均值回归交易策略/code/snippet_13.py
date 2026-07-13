def get_buy_price(context):
    sel_stock_price = attribute_history(g.sel_stock, 1, unit='50m', fields=('open','close','high','low'), skip_paused=True, df=True, fq='pre')
    if context.current_dt.time() >= g.strategy_starttime and context.current_dt.time() < g.strategy_endtime:
        return sel_stock_price['low'][0]
    else:
        return sel_stock_price['close'][0]
def get_sell_price(context):
    sel_stock_price = attribute_history(g.sel_stock, 1, unit='50m', fields=('open','close','high','low'), skip_paused=True, df=True, fq='pre')
    if context.current_dt.time() >= g.strategy_starttime and context.current_dt.time() < g.strategy_endtime:
        return sel_stock_price['high'][0]
    else:
        return sel_stock_price['close'][0]

复制
