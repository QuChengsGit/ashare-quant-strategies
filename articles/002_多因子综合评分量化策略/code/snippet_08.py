def get_stock_list(context):
    ...
    # 获得初始列表
    yesterday = context.previous_date
    initial_list = get_all_securities('stock', yesterday).index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_new_stock(context, initial_list, 375)
    initial_list = filter_st_stock(initial_list)
    # 使用财务指标过滤股票
    q = query(
        valuation.code, valuation.market_cap, valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(initial_list),
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    ).order_by(valuation.market_cap.asc()).limit(100)
    df = get_fundamentals(q, date=yesterday)
    # 计算得分并排序
    ...
    df['score'] = temp_list
    df = df.sort_values(by='score', ascending=False)
    return list(df.index)

复制
