def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    factor1_list = get_factor_filter_list(context, initial_list, g.factor1, g.sort1, g.P1)
    factor2_list = get_factor_filter_list(context, factor1_list, g.factor2, g.sort2, g.P2)
    factor3_list = get_factor_filter_list(context, factor2_list, g.factor3, g.sort3, g.P3)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
        valuation.code.in_(factor3_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q).dropna()
    return list(df[df['eps'] > 0].code)
