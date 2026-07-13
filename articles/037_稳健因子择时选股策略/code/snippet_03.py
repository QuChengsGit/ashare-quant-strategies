def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)  # 过滤科创板和北交所股票
    initial_list = filter_st_stock(initial_list)  # 过滤ST股票
    initial_list_1 = filter_new_stock(context, initial_list, 250)  # 过滤次新股
    # 长期资产回报率筛选
    roa_list = get_factor_filter_list(context, initial_list_1, 'roa_ttm_8y', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(roa_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    roa_list = list(df[df['eps'] > 0].code)[:5]
    # 每股留存收益筛选
    reps_list = get_factor_filter_list(context, initial_list_1, 'retained_earnings_per_share', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(reps_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    reps_list = list(df[df['eps'] > 0].code)[:5]
    # 非线性市值筛选
    initial_list_2 = filter_new_stock(context, initial_list, 125)
    nls_list = get_factor_filter_list(context, initial_list_2, 'non_linear_size', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(nls_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    nls_list = list(df[df['eps'] > 0].code)[:5]
    # 取并集去重
    union_list = list(set(roa_list).union(set(reps_list)).union(set(nls_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    return list(get_fundamentals(q, date=yesterday).code)
