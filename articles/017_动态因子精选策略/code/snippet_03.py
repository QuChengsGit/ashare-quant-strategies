def prepare_stock_list(context):
    g.hold_list = list(context.portfolio.positions)
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        temp_set = temp_set.union(set(hold_list))
    g.not_buy_again_list = list(temp_set)
    g.high_limit_list = []
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily', fields=['close', 'high_limit', 'paused'], count=1, panel=False)
        g.high_limit_list = df.query('close==high_limit and paused==0')['code'].tolist()
