def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    factor_values = get_factor_values(initial_list, [
        g.factor_list[0],
        g.factor_list[1],
        g.factor_list[2],
        ], end_date=yesterday, count=1)
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df[g.factor_list[0]] = list(factor_values[g.factor_list[0]].T.iloc[:,0])
    df[g.factor_list[1]] = list(factor_values[g.factor_list[1]].T.iloc[:,0])
    df[g.factor_list[2]] = list(factor_values[g.factor_list[2]].T.iloc[:,0])
    df = df.dropna()
    coef_list = [
        -6.123355346008858e-05,
        -0.002579342458393642,
        -2.194257357346814e-06
        ]
    df['total_score'] = coef_list[0]*df[g.factor_list[0]] + coef_list[1]*df[g.factor_list[1]] + coef_list[2]*df[g.factor_list[2]]
    df = df.sort_values(by=['total_score'], ascending=False)
    complex_factor_list = list(df.index)[:max(int(0.1*len(list(df.index))),g.stock_num)]
    q = query(valuation.code,valuation.circulating_market_cap,indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    df = df[df['eps']>0]
    final_list  = list(df.code)
    final_list = filter_paused_stock(final_list)
    final_list = filter_limitup_stock(context, final_list)
    final_list = filter_limitdown_stock(context, final_list)
    return final_list

复制
