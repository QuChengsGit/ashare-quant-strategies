def get_stock_list(context):
    # 获取昨日和今天的日期
    yesterday = context.previous_date
    today = context.current_dt
    # 获取所有股票的列表
    initial_list = get_all_securities('stock', today).index.tolist()
    # 过滤不符合条件的股票
    initial_list = filter_all_stock2(context, initial_list)
    final_list = []
    # 获取因子列表
    factor_list = list(g.factor_list[0].keys())
    # 获取因子数据
    factor_data = get_factor_values(initial_list, factor_list, end_date=yesterday, count=1)
    df_jq_factor_value = pd.DataFrame(index=initial_list, columns=factor_list)
    for factor in factor_list:
        df_jq_factor_value[factor] = list(factor_data[factor].T.iloc[:, 0])
    # 对因子数据进行标准化处理
    df_jq_factor_value = data_preprocessing(df_jq_factor_value, initial_list, industry_code, yesterday)
    df = df_jq_factor_value
    df = df.dropna()  # 去除缺失值
    # 根据选择的因子筛选股票
    for factor in g.chosen_factor:
        df = df[(df[factor] >= g.factor_list[0][factor][0]) & (df[factor] <= g.factor_list[0][factor][1])]
        print(f'过滤完 {factor} ，剩余：{len(df)}')
    postive_list = list(df.index)  # 选定的股票列表
    log.info(f'因子筛选后的数量：{len(postive_list)}/{len(df)}')
    # 根据市值进行排序，选择市值较小的股票
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(postive_list)).order_by(valuation.circulating_market_cap.asc())
    df2 = get_fundamentals(q)
    df2 = df2[df2['eps'] > 0]
    lst = list(df2.code)
    # 选择前N只股票
    lst = lst[:min(g.stock_num, len(lst))]
    # 添加到最终选股列表
    for stock in lst:
        if stock not in final_list:
            final_list.append(stock)
    return final_list
