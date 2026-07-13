def set_stockpool(context):
    stocks2 = get_index_stocks('000300.XSHG')
    paused_series = get_price(stocks2, end_date=context.current_dt, count=1, fields='paused')['paused'].iloc[0]
    g.stock_pool = paused_series[paused_series == False].index.tolist()

复制
