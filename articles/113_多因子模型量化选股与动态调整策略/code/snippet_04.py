def get_stock_list(context):
    by_date = context.previous_date - datetime.timedelta(days=375)
    initial_list = get_all_securities(date=by_date).index.tolist()
    initial_list = filter_kcb_stock(initial_list)
    initial_list = filter_st_stock(initial_list)
    # 使用多种因子进行选股
    sg_list = get_single_factor_list(context, initial_list, 'sales_growth', False, 0, 0.1)
    sg_list = sorted_by_circulating_market_cap(sg_list)
    # 更多因子选股
    # ...
    # 返回并集的前12只股票
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    union_list = sorted_by_circulating_market_cap(union_list, 12)
    print('选股结果：', union_list)
    return union_list
