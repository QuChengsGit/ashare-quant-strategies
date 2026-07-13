def get_stock_list(context):
    # 去掉次新股
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 过滤科创板和ST股
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 1. 扣非利润比前30%
    sg_list = get_single_factor_list(context, initial_list, 'adjusted_profit_to_total_profit', False, 0, 0.3)
    # 2. 综合成长因子
    factor_list = [
        'short_term_predicted_earnings_growth',
        'long_term_predicted_earnings_growth',
        'net_profit_growth_rate',
        'earnings_growth'
    ]
    factor_values = get_factor_values(sg_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=sg_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.2 * df['short_term_predicted_earnings_growth'] + 0.4 * df['long_term_predicted_earnings_growth'] + 0.2 * df['net_profit_growth_rate'] + 0.2 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.08 * len(df))].tolist()
    # 3. 综合PEG和市值筛选
    peg_list = get_single_factor_list(context, ms_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, ms_list, 'turnover_volatility', True, 0, 0.8)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    return peg_list
