def get_stock_list(context):
    # 获得初始列表
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 375)
    initial_list = filter_st_stock(initial_list)
    q = query(
        valuation.code, valuation.market_cap, valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(initial_list),
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    ).order_by(
        valuation.market_cap.asc()).limit(100)
    df = get_fundamentals(q, date=yesterday)
    df.index = df.code
    # 计算合成因子并排序
    df['score'] = df.apply(lambda row: sum([
        g.weights[0] * math.log(df['market_cap'].min() / row['market_cap']),
        g.weights[1] * math.log(df['circulating_market_cap'].min() / row['circulating_market_cap']),
        g.weights[2] * math.log(df['price_now'].min() / row['price_now']),
        g.weights[3] * math.log(df['total_volume_n'].min() / row['total_volume_n']),
        g.weights[4] * math.log(df['m_days_return'].min() / row['m_days_return'])
    ]), axis=1)
    df = df.sort_values(by='score', ascending=False)
    final_list = list(df.index)
    return final_list

复制
