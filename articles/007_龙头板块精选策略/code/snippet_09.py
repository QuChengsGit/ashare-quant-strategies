def get_stock_list(context):
    # 文本日期
    date = transform_date(context.previous_date, 'str')
    # 获取初始股票池
    initial_list = prepare_stock_list(date)
    # 获取涨停股票
    hl_list = get_hl_stock(initial_list, date)
    # 获取连板股票
    ccd = get_continue_count_df(hl_list, date, 20) if len(hl_list) != 0 else pd.DataFrame(index=[], data={'count':[], 'extreme_count':[]})
    # 筛选龙头股票
    M = ccd['count'].max() if len(ccd) != 0 else 0
    CCD = ccd[ccd['count'] == M] if M != 0 else pd.DataFrame(index=[], data={'count':[], 'extreme_count':[]})
    lt = list(CCD.index)
    # 因子筛选
    df = get_factor_filter_df(context, lt, g.jqfactor, g.sort)
    stock_list = list(df.index)
    # 根据持仓情况截取股票列表
    g.target_list = stock_list[:(g.ps - len(context.portfolio.positions))]

复制
