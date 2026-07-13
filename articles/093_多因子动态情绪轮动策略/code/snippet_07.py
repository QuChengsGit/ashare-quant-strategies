def get_stock_list(context):
    stat_date = context.current_dt.strftime('%Y-%m-%d')
    df = get_all_securities(types=['stock'], date=stat_date)
    stock_list = list(df.index)
    stock_list = filter_new_stock(context, stock_list, stat_date, g.fn)
    stock_list0 = filter_st_stock(context, stock_list, stat_date)
    stock_list1 = filter_hl_stock(context, stock_list0, stat_date)
    if len(stock_list1) != 0:
        stock_list = stock_list1
    else:
        stock_list = stock_list0
    continue_count_df = []
    days_count = g.watch_days + 1
    while len(continue_count_df) == 0:
        days_count -= 1
        if days_count <= 1:
            break
        else:
            MKT_df = limit_count(context, stock_list, stat_date, days_count)
            continue_count_df = MKT_df[MKT_df['count'] == days_count]
    if days_count > 1:
        smallest_stock = get_smallest(context, list(continue_count_df['code']), stat_date)
        count_df = continue_count_df.copy()
        count_df.index = count_df['code']
        limit_counts = count_df.loc[smallest_stock]['count']
        g.count_list.append(limit_counts)
        if len(g.count_list) > (g.emo_cycle - 1):
            emotion = g.count_list[-1] - max(g.count_list[-g.emo_cycle:])
        else:
            emotion = -100
    else:
        limit_counts = 0        
        emotion = -100
        g.count_list.append(limit_counts)                
    if emotion == 0:
        g.code_list.append(smallest_stock)       
        if g.code_list[-1] != g.code_list[-2]:
            g.buy_stock = smallest_stock
        else:
            g.buy_stock = 0
    else:
        g.buy_stock = 0
    if g.buy_stock != 0:
        q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code == g.buy_stock)
        df = get_fundamentals(q, date=stat_date)
        df = df[(df['circulating_market_cap'] > 20) & (df['circulating_market_cap'] < 80)]
        if len(df) == 0:
            g.buy_stock = 0
    if g.buy_stock != 0:
        if (limit_counts < 4) or (limit_counts > 8):
            g.buy_stock = 0
    print(g.buy_stock)
    return g.buy_stock
