def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 获取因子值
    factor_values = get_factor_values(initial_list, g.factor_list, end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=g.factor_list)
    for factor in g.factor_list:
        df[factor] = factor_values[factor].T.iloc[:, 0]
    df = df.dropna()
    # 因子加权计算总得分
    coef_list = [-6.123e-05, -0.002579, -2.194e-06]
    df['total_score'] = sum(coef * df[factor] for coef, factor in zip(coef_list, g.factor_list))
    # 根据得分排序并筛选前10%的股票
    df = df.sort_values(by='total_score', ascending=False)
    top_stocks = df.index[:int(0.1 * len(df.index))]
    # 进一步筛选流通市值和盈利状况
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(top_stocks)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    final_list = df[df['eps'] > 0].code.tolist()
    return final_list
