def get_single_factor_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    s_score = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].dropna().sort_values(ascending=sort)
    return s_score.index[int(p1 * len(stock_list)):int(p2 * len(stock_list))].tolist()
def sorted_by_circulating_market_cap(stock_list, n_limit_top=5):
    q = query(valuation.code).filter(valuation.code.in_(stock_list), indicator.eps > 0).order_by(valuation.circulating_market_cap.asc()).limit(n_limit_top)
    return get_fundamentals(q)['code'].tolist()
def get_stock_list(context):
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    sg_list = get_single_factor_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    sg_list = sorted_by_circulating_market_cap(sg_list)
    factor_list = ['operating_revenue_growth_rate', 'total_profit_growth_rate', 'net_profit_growth_rate', 'earnings_growth']
    factor_values = get_factor_values(initial_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=initial_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.15 * df['total_profit_growth_rate'] + 0.15 * df['net_profit_growth_rate'] + 0.6 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.1 * len(df))].tolist()
    ms_list = sorted_by_circulating_market_cap(ms_list)
    peg_list = get_single_factor_list(context, initial_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    union_list = sorted_by_circulating_market_cap(union_list, 12)
    print('选股结果：', union_list)
    return union_list

复制
