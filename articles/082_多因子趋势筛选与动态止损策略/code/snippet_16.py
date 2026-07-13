def lost_control(context, stocklist, check_date):
    poollist = []
    for stockcode in context.portfolio.positions:
        cost = context.portfolio.positions[stockcode].avg_cost
        price = context.portfolio.positions[stockcode].price
        ret = price / cost
        # 动态止损判断
        if g.lostcontrol == 2:
            df_price = get_price(stockcode, count=g.drop_ma_days, end_date=context.previous_date, frequency='daily', fields=['high', 'close'])
            high_max = df_price['high'].max()
            last_price = df_price['close'].values[-1]
            if last_price / high_max < g.drop_line:
                poollist.append(stockcode)
    return poollist

复制
