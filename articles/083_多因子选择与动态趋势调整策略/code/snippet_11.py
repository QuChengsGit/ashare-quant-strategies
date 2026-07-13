def get_stock_list(context):
    # 去掉次新股
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    # 去除科创板及ST股票
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 1. 筛选营业收入增长率最高的股票，并按流通市值筛选
    sg_list = get_single_factor_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    sg_list = sorted_by_circulating_market_cap(sg_list)
    # 2. 综合多个增长率因子，计算总评分并筛选
    factor_list = [
        'operating_revenue_growth_rate',  # 营业收入增长率
        'total_profit_growth_rate',  # 利润总额增长率
        'net_profit_growth_rate',  # 净利润增长率
        'earnings_growth',  # 5年盈利增长率
    ]
    factor_values = get_factor_values(initial_list, factor_list, end_date=context.previous_date, count=1)
    df = pd.DataFrame(index=initial_list)
    for factor in factor_list:
        df[factor] = factor_values[factor].iloc[0]
    df['total_score'] = 0.1 * df['operating_revenue_growth_rate'] + 0.35 * df['total_profit_growth_rate'] + 0.15 * df[
        'net_profit_growth_rate'] + 0.4 * df['earnings_growth']
    ms_list = df.sort_values(by=['total_score'], ascending=False).index[:int(0.1 * len(df))].tolist()
    ms_list = sorted_by_circulating_market_cap(ms_list)
    # 3. 筛选PEG最低的股票，并按流通市值筛选
    peg_list = get_single_factor_list(context, initial_list, 'PEG', True, 0, 0.2)
    peg_list = get_single_factor_list(context, peg_list, 'turnover_volatility', True, 0, 0.5)
    peg_list = sorted_by_circulating_market_cap(peg_list)
    # 将以上三组股票合并，并按流通市值排序
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    union_list = sorted_by_circulating_market_cap(union_list, 100)
    print('选股结果：', union_list)
    return union_list

复制
