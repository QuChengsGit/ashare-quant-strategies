def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcbj_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 用因子获取昨日收盘价并筛选
    price_list1 = get_factor_filter_list(context, initial_list, 'price_no_fq', True, 0, 0.1)
    # 通过流通市值和每股收益进一步筛选
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(price_list1)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q, date=yesterday)
    df = df[df['eps'] > 0]
    final_list = list(df.code)[:15]
    return final_list
