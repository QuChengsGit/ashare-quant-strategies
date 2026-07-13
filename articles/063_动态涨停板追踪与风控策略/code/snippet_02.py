def market_run(context):
    time_now = context.current_dt.strftime('%H:%M:%S')
    if time_now <= '09:31:00':
        return
    cash = context.portfolio.available_cash
    if cash > 5000 and len(context.portfolio.positions) < g.max_stock_num:
        bars = get_bars(list(g.help_stock.keys()), count=2, unit='1m', fields=['close'], include_now=True, end_dt=context.current_dt)
        for stock in g.help_stock:
            if stock in context.portfolio.positions:
                continue
            close2m = bars[stock]['close']
            if close2m[-2] < close2m[-1] == g.help_stock[stock]:
                function_buy(context, stock)
    # 卖出条件判断与执行
    holdings = [s for s in context.portfolio.positions if context.portfolio.positions[s].closeable_amount > 0]
    if not holdings:
        return
    # 获取昨日和今日的数据
    df_pre = get_price(holdings, count=1, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], panel=False).set_index('code')
    today_start = context.current_dt.replace(hour=9, minute=31, second=0)
    df_all_day = get_price(holdings, start_date=today_start, end_date=context.current_dt,
                           frequency='1m', fields=['high', 'close', 'high_limit'], panel=False)
    s_high_today = df_all_day.groupby('code')['high'].max()
    s_count_limit_all_day = df_all_day.groupby('code').apply(lambda x: (x.close == x.high_limit).sum())
    s_count_limit_first_10m = df_all_day.groupby('code').apply(lambda x: (x.close == x.high_limit)[:10].sum())
    curr_data = get_current_data()
    for stock in holdings:
        current_price = curr_data[stock].last_price
        day_open_price = curr_data[stock].day_open
        day_high_limit = curr_data[stock].high_limit
        day_low_limit = curr_data[stock].low_limit
        if current_price <= day_low_limit:
            continue
        pre_close = df_pre['close'][stock]
        pre_high_limit = df_pre['high_limit'][stock]
        high_all_day = s_high_today[stock]
        count_limit_all_day = s_count_limit_all_day[stock]
        count_limit_before10 = s_count_limit_first_10m[stock]
        cost = context.portfolio.positions[stock].avg_cost
        # 一系列卖出条件
        if current_price >= cost * 2:
            order_target(stock, 0)
        elif current_price < cost * 0.92 and current_price < day_open_price and pre_close == pre_high_limit:
            order_target(stock, 0)
        # ...（其他卖出条件）
        elif day_open_price > pre_close * 1.045 and current_price < day_open_price and time_now <= '09:33:00':
            order_target(stock, 0)
