def get_stock_list(context):
    """
    选股模块：基于行业宽度和财务指标筛选股票
    """
    yesterday = context.previous_date
    today = context.current_dt
    # 获取中证全指成分股作为初始股票池
    initial_list = get_index_stocks('000985.XSHG', today)
    # 获取股票价格数据并计算20日均线
    h = get_price(initial_list,
                 end_date=yesterday,
                 frequency='1d',
                 fields=['close'],
                 count=21,
                 panel=False)
    df_close = h.pivot(index='code', columns='date', values='close').dropna(axis=0)
    df_ma20 = df_close.rolling(window=20, axis=1).mean().iloc[:, -1:]
    # 判断收盘价是否高于20日均线
    df_bias = (df_close.iloc[:, -1:] > df_ma20)
    # 获取股票行业分类
    s_stk_2_ind = getStockIndustry(p_stocks=initial_list, p_industries_type='sw_l1', p_day=yesterday)
    df_bias['industry_code'] = s_stk_2_ind
    # 计算各行业价格高于均线的股票比例
    df_ratio = (df_bias.groupby('industry_code').sum() * 100.0 / df_bias.groupby('industry_code').count()).round()
    # 选择表现最好的行业
    top_industries = df_ratio.iloc[:, -1].nlargest(g.num).index.tolist()
    # 过滤行业，并使用财务指标进行进一步筛选
    all_stocks = get_all_securities('stock', today).index.tolist()
    sz_stocks = [stock for stock in all_stocks if stock.startswith('002')]  # 选择深市股票
    # 使用财务筛选进一步筛选
    q = query(valuation.code).filter(valuation.code.in_(sz_stocks), valuation.pb_ratio > 0)
    final_list = get_fundamentals(q).set_index('code').index.tolist()
    return final_list


get_index_stocks('000985.XSHG', today)：获取中证全指（或其它指数）的成分股作为初步筛选的股票池。
