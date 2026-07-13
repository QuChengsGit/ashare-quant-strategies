def get_stock_list(context):
    yesterday = context.previous_date
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤科创板、ST股票
    initial_list = filter_kcb_stock(initial_list)
    sample = filter_st_stock(initial_list)
    # 计算FCF/市值和ROE因子
    q = query(
        valuation.code,
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / 100000000,
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000),
        indicator.roe,
        indicator.net_profit_margin,
        indicator.inc_net_profit_year_on_year,
        valuation.circulating_market_cap
    ).filter(
        valuation.code.in_(sample),
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000) > 0.02,
        indicator.adjusted_profit > 0,
        indicator.roe > 3,
        indicator.net_profit_margin > 10,
        indicator.inc_net_profit_to_shareholders_year_on_year > 5
    ).order_by(
        (cash_flow.net_operate_cash_flow - cash_flow.subtotal_invest_cash_outflow) / (valuation.market_cap * 100000000).desc()
    )
    df = get_fundamentals(q)
    df.columns = ['code', '自由现金流（亿元）', 'FCF/市值(排序列)', 'roe', '净利率', '归母净利润YOY', '流通市值']
    df.index = df['code']
    df.drop(columns=['code'], inplace=True)
    # 因子处理：去极值、中性化、标准化
    factors_list = ['FCF/市值(排序列)', 'roe']
    df['score'] = 0
    for factor in factors_list:
        df[factor] = winsorize(df[factor], qrange=[0.05, 0.93])
        df[factor] = neutralize(df[factor], how=['jq_l1', 'market_cap'])
        df[factor] = standardlize(df[factor])
        df['score'] += df[factor]
    # 根据得分排序，选出前10个股票
    df_sorted = df.sort_values('score', ascending=False).iloc[:10]
    return df_sorted.index.tolist()

复制
