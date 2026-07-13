def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    x_list = get_factor_filter_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(x_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps'] > 0]
    final_list = list(df.code)
    return final_list

复制
