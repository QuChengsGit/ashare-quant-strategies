def buy(context):
    long_cash = context.portfolio.total_value
    if not g.buy.empty:
        for s in g.buy.index:
            order_target_value(s, g.buy.loc[s] * 0.5 * long_cash)
def sell(context):
    for s in context.portfolio.positions.keys():
        order_target_value(s, 0)
