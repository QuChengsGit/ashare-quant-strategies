def get_factor_filter_list(context, stock_list, jqfactor, sort, p):
    yesterday = context.previous_date
    score_list = get_factor_values(stock_list, jqfactor, end_date=yesterday, count=1)[jqfactor].iloc[0].tolist()
    df = pd.DataFrame(columns=['code', 'score'])
    df['code'] = stock_list
    df['score'] = score_list
    df = df.dropna()
    df = df[df['score'] > 0]
    df.sort_values(by='score', ascending=sort, inplace=True)
    filter_list = list(df.code)[0:int(p * len(stock_list))]
    return filter_list
def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    profit_growth_list = get_factor_filter_list(context, initial_list, 'net_profit_growth_rate', False, 0.1)
    peg_list = get_factor_filter_list(context, profit_growth_list, 'PEG', True, 0.5)
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(peg_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    final_list = list(df.code)
    return final_list

复制
