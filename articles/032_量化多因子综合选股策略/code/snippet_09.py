def get_stock_list(context):
    # 获取股票的基本面数据
    q = query(
        valuation.code,
        valuation.pe_ratio,
        valuation.pb_ratio,
        indicator.inc_return,
        indicator.inc_total_revenue_year_on_year,
        indicator.inc_net_profit_year_on_year,
        valuation.market_cap
    ).filter(
        valuation.pe_ratio > 0,
        valuation.pb_ratio > 0,
        indicator.inc_return > 0,
        indicator.inc_total_revenue_year_on_year > 0,
        indicator.inc_net_profit_year_on_year > 0
    )
    df = get_fundamentals(q)
    df = pd.DataFrame(df).dropna().sort_values(by='market_cap', ascending=False)
    print('本月股票总数: %s' % len(df))
    # 选取前N%的股票
    df = select_top_percent_stocks(df, g.stock_selection_percent)
    print('本月选中股票总数: {}% ({})'.format(g.stock_selection_percent * 100, len(df)))
    stock_list = list(df['code'])
    # 对股票列表进行多维度过滤
    stock_list = filter_st_stock(stock_list)
    stock_list = filter_paused_stock(stock_list)
    stock_list = filter_limitup_stock(context, stock_list)
    stock_list = filter_limitdown_stock(context, stock_list)
    stock_list = filter_kcbj_stock(stock_list)
    stock_list = ffscore_stock(context, g.score, stock_list, context.current_dt.date())
    print('本月股票池 %s 个' % len(stock_list))
    return stock_list

复制
