def before_closing(context):
    sell_before_closing(context)
def sell_before_closing(context):
    df = history(1,'1d','close',context.portfolio.positions.keys())
    for s in list(context.portfolio.positions):
        if context.portfolio.positions[s].closeable_amount<=0:
            continue
        close_data = get_bars(s, count=2, unit='1m', fields=['open','high','low','close'],include_now=False)
        close_price = close_data['close'][-1]
        # 1.没涨停，卖
        if close_price/df[s][0]<1.098:
            R = order_target(s, 0)
        # 其他条件逻辑...
