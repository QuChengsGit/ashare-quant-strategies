def get_stock_list(context):
    yesterday = context.previous_date
    # 定义国企股票列表
    stocklists = [
        '601919.XSHG', '300073.XSHE', '600536.XSHG', '000951.XSHE',
        '601628.XSHG', '600036.XSHG', '601818.XSHG', '001289.XSHE',
        ...
        '600029.XSHG', '002916.XSHE', '301269.XSHE', '600482.XSHG'
    ]
    stocklists = filter_st_stock(stocklists)  # 过滤ST股
    # 根据预期增长率剔除后15%的股票
    factor_data = get_factor_values(securities=stocklists, factors=['growth'], end_date=yesterday, count=1)['growth'].iloc[0]
    growth_list = factor_data.sort_values(ascending=False).index.tolist()
    growth_list = growth_list[:int(len(growth_list) * 0.80)]
    # 根据PE和PB复合排序并考虑行业比重
    df = get_valuation(growth_list, end_date=yesterday, fields=['pe_ratio', 'pb_ratio'], count=1).set_index('code')
    df['sw_code'] = ''
    industry_data = get_industry(security=growth_list, date=context.previous_date)
    for stock in growth_list:
        df.loc[stock, 'sw_code'] = industry_data[stock].get('sw_l1')['industry_code']
    # 筛选特定行业股票并计算综合评分
    df = df[df['sw_code'].isin(['801180', '801780', '801790', '801720'])]
    df['dense'] = df.groupby('sw_code')['pb_ratio'].rank(method='min', ascending=True, pct=True)
    df['score'] = df['dense'] * 0.8 + df.pe_ratio.rank(method='min', ascending=True, pct=True) * 0.2
    # 按评分排序并选择前N只股票作为目标股票池
    pb_list = df.sort_values('score', ascending=True).index.tolist()
    g.target_list = pb_list[:g.stock_num + 2]  # 多选2只以备不时之需
    return g.target_list
