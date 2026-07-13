def get_factor_filter_list(context, stock_list, jqfactor, sort, p1, p2):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame({'code': stock_list, 'score': score_list}).dropna()
    df.sort_values(by='score', ascending=sort, inplace=True)
    return list(df.code)[int(p1*len(df)):int(p2*len(df))]
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    initial_list_1 = filter_new_stock(context, initial_list, 250)
    # 筛选长期毛利率增长最小的前10%股票
    test_list = get_factor_filter_list(context, initial_list_1, 'DEGM_8y', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    roa_list = list(df[df['eps']>0].code)[:5]
    # 筛选每股净资产最小的前10%股票
    test_list = get_factor_filter_list(context, initial_list_1, 'net_asset_per_share', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    reps_list = list(df[df['eps']>0].code)[:5]
    # 筛选非线性市值最小的前10%股票
    initial_list_2 = filter_new_stock(context, initial_list, 125)
    test_list = get_factor_filter_list(context, initial_list_2, 'non_linear_size', True, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(test_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    nls_list = list(df[df['eps']>0].code)[:5]
    # 并集去重后，返回按流通市值排序的最终列表
    union_list = list(set(roa_list).union(set(reps_list)).union(set(nls_list)))
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(union_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=context.previous_date)
    return list(df.code)
