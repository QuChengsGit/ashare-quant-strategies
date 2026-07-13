def prepare_trade(context):
    g.hold_list = list(context.portfolio.positions.keys())
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)
