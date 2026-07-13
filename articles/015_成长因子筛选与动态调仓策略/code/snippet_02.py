def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    factor_values = get_factor_values(initial_list, [
        'operating_revenue_growth_rate',  # 营业收入增长率
        'total_profit_growth_rate',       # 利润总额增长率
        'earnings_growth',                # 五年盈利增长率
    ], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list)
    df['operating_revenue_growth_rate'] = list(factor_values['operating_revenue_growth_rate'].T.iloc[:, 0])
    df['total_profit_growth_rate'] = list(factor_values['total_profit_growth_rate'].T.iloc[:, 0])
    df['earnings_growth'] = list(factor_values['earnings_growth'].T.iloc[:, 0])
    df['total_score'] = (0.2 * df['operating_revenue_growth_rate'] +
                         0.4 * df['total_profit_growth_rate'] +
                         0.4 * df['earnings_growth'])
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_growth_list = list(df.index)[:int(0.1 * len(df.index))]
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_growth_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps'] > 0]
    return list(df.code)
