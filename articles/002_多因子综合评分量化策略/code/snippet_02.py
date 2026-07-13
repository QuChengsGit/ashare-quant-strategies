def prepare_stock_list(context):
    g.hold_list= []
    for position in list(context.portfolio.positions.values()):
        g.hold_list.append(position.security)
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close','high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.high_limit_list = []
