def before_market_open(context):
    yesterday = context.previous_date
    list_date = get_before_after_trade_days(yesterday, g.moment_period+1)
    g.ETFList = {}
    all_funds = get_all_securities(types='fund', date=yesterday)
    for idx in g.ETF_targets:
        symbol = g.ETF_targets[idx]
        if symbol in all_funds.index and all_funds.loc[symbol].start_date <= list_date:
            g.ETFList[idx] = symbol
