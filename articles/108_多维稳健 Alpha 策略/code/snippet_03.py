def get_stock_list(context):
    yesterday = str(context.previous_date)
    initial_list = get_all_securities().index.tolist()  # 获取所有股票
    initial_list = filter_new_stock(context, initial_list)  # 过滤掉新股
    initial_list = filter_kcb_stock(context, initial_list)  # 过滤科创板股票
    initial_list = filter_st_stock(initial_list)  # 过滤掉ST股
    # PB过滤
    q = query(valuation.code, valuation.pb_ratio, indicator.eps).filter(valuation.code.in_(initial_list)).order_by(valuation.pb_ratio.asc())
    df = get_fundamentals(q)  # 获取PB和EPS数据
    df = df[df['eps'] > 0]  # 只保留盈利大于0的股票
    df = df[df['pb_ratio'] > 0]  # 只保留PB大于0的股票
    pb_list = list(df.code)[:int(0.5 * len(df.code))]  # 选取PB最小的一半股票
    # ROE过滤
    interval = 1000
    pb_len = len(pb_list)
    if pb_len <= interval:
        df = get_history_fundamentals(pb_list, fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
    else:
        df_num = pb_len // interval
        df = get_history_fundamentals(pb_list[:interval], fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
        for i in range(df_num):
            dfi = get_history_fundamentals(pb_list[interval*(i+1):min(pb_len,interval*(i+2))], fields=[indicator.code, indicator.roe], watch_date=yesterday, count=5, interval='1q')
            df = df.append(dfi)
    df = df.groupby('code').apply(lambda x: x.reset_index()).roe.unstack()  # 获取ROE数据
    df['increase'] = 4 * df.iloc[:, 4] - df.iloc[:, 0] - df.iloc[:, 1] - df.iloc[:, 2] - df.iloc[:, 3]  # 计算ROE的增长量
    df.dropna(inplace=True)  # 删除缺失值
    df.sort_values(by='increase', ascending=False, inplace=True)  # 按照ROE增长排序
    temp_list = list(df.index)
    temp_len = len(temp_list)
    roe_list = temp_list[:int(0.1 * temp_len)]  # 选取ROE增长前10%的股票
    # 行业过滤
    if g.industry_control:
        industry_df = get_stock_industry(roe_list, yesterday)
        ROE_list = filter_industry(industry_df, g.industry_filter_list)
    else:
        ROE_list = roe_list
    # 市值排序
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.code.in_(ROE_list)).order_by(valuation.circulating_market_cap.asc())
    df = get_fundamentals(q)  # 获取市值数据
    ROEC_list = list(df.code)
    return ROEC_list
