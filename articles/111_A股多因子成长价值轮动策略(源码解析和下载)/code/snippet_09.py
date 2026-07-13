def my_trade(context):
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
    g.hold_list = list(context.portfolio.positions.keys())
    if g.no_trading_today_signal: return
