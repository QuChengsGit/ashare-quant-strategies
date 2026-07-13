def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = list(set(get_all_securities().index) & set(get_hot_industry_stock(context)))
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    # 筛选财务增长因子股票
    sg_list = get_factor_filter_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    # 综合成长因子筛选
    factor_values = get_factor_values(initial_list, ['operating_revenue_growth_rate', 'total_profit_growth_rate', 'net_profit_growth_rate', 'earnings_growth'], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:, 0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:, 0])
    df['net_profit_growth_rate'] = list(factor_values['net_profit_growth_rate'].T.iloc[:, 0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:, 0])
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.35 * df['total_profit_growth_rate'] + 0.15 * df['net_profit_growth_rate'] + 0.4 * df['earnings_growth']
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_growth_list = list(df.index)[:int(0.1 * len(list(df.index)))]
    # 筛选PEG因子股票
    peg_list = get_factor_filter_list(context, initial_list, 'PEG', True, 0, 0.2)
    turnover_list = get_factor_filter_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    final_list = [sg_list, list(df.code), peg_list]
    return final_list

复制
