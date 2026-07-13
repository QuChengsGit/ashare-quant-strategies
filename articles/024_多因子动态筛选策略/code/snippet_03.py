def get_stock_list(context):
    yesterday = context.previous_date
    today = context.current_dt
    initial_list = get_all_securities('stock', today).index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    final_list = []
    for factor_list, coef_list in g.factor_list:
        factor_values = get_factor_values(initial_list, factor_list, end_date=yesterday, count=1)
        df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
        for i in range(len(factor_list)):
            df[factor_list[i]] = list(factor_values[factor_list[i]].T.iloc[:, 0])
        df = df.dropna()
        df['total_score'] = sum(coef_list[i] * df[factor_list[i]] for i in range(len(factor_list)))
        df = df[df['total_score'] > 0].sort_values(by='total_score', ascending=False)
        complex_factor_list = list(df.index)[:int(0.1 * len(df))]
        q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
        df = get_fundamentals(q)
        df = df[df['eps'] > 0]
        lst = filter_paused_stock(list(df.code))
        lst = filter_limitup_stock(context, lst)
        lst = filter_limitdown_stock(context, lst)
        lst = lst[:min(g.stock_num, len(lst))]
        final_list.extend([stock for stock in lst if stock not in final_list])
    return final_list
