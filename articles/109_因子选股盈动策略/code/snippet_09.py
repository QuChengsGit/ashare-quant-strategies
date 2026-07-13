def get_stock_list(context):
    yesterday = context.previous_date  # 获取昨日的日期
    initial_list = get_all_securities().index.tolist()  # 获取所有股票代码
    initial_list = filter_new_stock(context, initial_list)  # 过滤新股
    initial_list = filter_kcbj_stock(initial_list)  # 过滤科创板股票
    initial_list = filter_st_stock(initial_list)  # 过滤ST股票
    # 获取因子值
    factor_values = get_factor_values(initial_list, [
        g.factor_list[0],
        g.factor_list[1],
        g.factor_list[2],
        g.factor_list[3],
    ], end_date=yesterday, count=1)  # 获取选定因子的值
    # 将因子值转换为DataFrame格式
    df = pd.DataFrame(index=initial_list, columns=factor_values.keys())
    df[g.factor_list[0]] = list(factor_values[g.factor_list[0]].T.iloc[:, 0])
    df[g.factor_list[1]] = list(factor_values[g.factor_list[1]].T.iloc[:, 0])
    df[g.factor_list[2]] = list(factor_values[g.factor_list[2]].T.iloc[:, 0])
    df[g.factor_list[3]] = list(factor_values[g.factor_list[3]].T.iloc[:, 0])
    # 删除缺失数据
    df = df.dropna()
    # 根据因子权重计算总得分
    coef_list = [-2.3425, -694.7936, -170.0463, -1362.5762]
    df['total_score'] = coef_list[0]*df[g.factor_list[0]] + coef_list[1]*df[g.factor_list[1]] + coef_list[2]*df[g.factor_list[2]] + coef_list[3]*df[g.factor_list[3]]
    # 按总得分降序排序，得分越高未来表现越好
    df = df.sort_values(by=['total_score'], ascending=False)
    # 选择前10%的股票
    complex_factor_list = list(df.index)[:int(0.1*len(list(df.index)))]
    # 获取股票的市值和每股收益
    q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(valuation.code.in_(complex_factor_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)
    # 过滤掉每股收益小于0的股票
    df = df[df['eps'] > 0]
    # 返回筛选后的股票列表
    final_list = list(df.code)
    return final_list

复制
