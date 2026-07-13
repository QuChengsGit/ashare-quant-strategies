def get_momentum(context, stock_list):
    stock_momentum = {}
    for stock in stock_list:
        # 计算股票的动量
        df = get_price(stock, count=g.day_count, end_date=context.current_dt - datetime.timedelta(days=1), fields=['close'], skip_paused=True, panel=False)
        if df['close'][-1] < g.stock_price:
            continue
        stock_momentum[stock] = (df['close'][-1] - df['close'][0]) / df['close'][0]
    # 返回动量最大的股票
    next_hold = min_dict(stock_momentum, g.stock_num)
    return next_hold
